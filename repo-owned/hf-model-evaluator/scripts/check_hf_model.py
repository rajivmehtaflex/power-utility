#!/usr/bin/env python3
"""Universal Hugging Face Model & Collection Hardware Evaluator.

Evaluates arbitrary Hugging Face model or collection URLs against local hardware
(CPU RAM, GPU VRAM, free disk space) and maps execution suitability for Colibri,
GGUF, and generic inference engines.

Zero external pip dependencies: uses Python standard library only.
"""

import argparse
import fnmatch
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

GB = 1_000_000_000
USER_AGENT = "hf-model-evaluator/1.0"

# Known Colibri engine families and heuristics
COLIBRI_FAMILIES = {
    "qwen36": {
        "patterns": ["qwen3.6*", "qwen3-coder*", "*qwen36*"],
        "model_types": ["qwen2", "qwen3", "qwen36", "qwen3_moe"],
        "has_cuda": True,
        "notes": "Runs from RAM if quantized (int4-gs64) fits, supports CUDA acceleration",
    },
    "qwen38": {
        "patterns": ["qwen3.8*", "qwen38*"],
        "model_types": ["qwen38", "qwen3_8"],
        "has_cuda": True,
        "notes": "MoE streaming or RAM, FP8 and int4 quants",
    },
    "deepseek_v4": {
        "patterns": ["*deepseek-v4*", "*dsv4*"],
        "model_types": ["deepseek_v4", "deepseek_v3"],
        "has_cuda": True,
        "notes": "Large MoE: dense part in RAM, streams experts from SSD",
    },
    "deepseek_v41": {
        "patterns": ["*deepseek-v4.1*", "*deepseek-v41*", "*dsv41*"],
        "model_types": ["deepseek_v41", "deepseek_v4_1"],
        "has_cuda": True,
        "notes": "Official V4.1 checkpoint with DSML reasoning formatting",
    },
    "glm": {
        "patterns": ["*glm-5.2*", "*glm-5.3*", "*glm-4*"],
        "model_types": ["chatglm", "glm", "glm_moe"],
        "has_cuda": True,
        "notes": "744B MoE architecture with MTP speculative decoding",
    },
    "kimi": {
        "patterns": ["*kimi-k3*", "*kimi*"],
        "model_types": ["kimi_k3", "kimi"],
        "has_cuda": True,
        "notes": "2.8T MoE architecture with native MXFP4 experts",
    },
    "mimo": {
        "patterns": ["*mimo-v2.6*", "*mimo*"],
        "model_types": ["mimo", "mimo_v2"],
        "has_cuda": True,
        "notes": "Vision + text MoE architecture",
    },
    "qwen_image": {
        "patterns": ["*qwen-image*"],
        "model_types": ["qwenimage21pipeline", "qwen_image"],
        "has_cuda": False,
        "notes": "Diffusion image synthesis model",
    },
    "inkling": {
        "patterns": ["*inkling*"],
        "model_types": ["inkling"],
        "has_cuda": True,
        "notes": "975B MoE, int4 experts with bf16 dense weights",
    },
    "olmoe": {
        "patterns": ["*olmoe*"],
        "model_types": ["olmoe"],
        "has_cuda": False,
        "notes": "Open MoE architecture with GGUF support",
    },
}


# ==============================================================================
# Environment & Hardware Diagnostics
# ==============================================================================

def get_hf_endpoint():
    return (os.environ.get("HF_ENDPOINT") or "https://huggingface.co").rstrip("/")


def get_hf_token():
    for name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACEHUB_API_TOKEN_READ"):
        val = os.environ.get(name)
        if val and val.strip():
            return val.strip()
    home = os.environ.get("HF_HOME") or os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
    token_file = os.path.join(home, "token")
    if os.path.isfile(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                t = f.read().strip()
                if t:
                    return t
        except OSError:
            pass
    # Check .env files (/content/.env or ./.env)
    for env_path in ("/content/.env", ".env"):
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    content = f.read()
                m = re.search(r'(?:export\s+)?(?:HUGGINGFACEHUB_API_TOKEN_READ|HF_TOKEN|HUGGING_FACE_HUB_TOKEN)\s*=\s*["\']?([^"\']+)["\']?', content)
                if m and m.group(1).strip():
                    return m.group(1).strip()
            except OSError:
                pass
    return None


def detect_memory():
    """Detects total and available system RAM in bytes."""
    mem = {"total_bytes": 0, "available_bytes": 0}
    if os.path.isfile("/proc/meminfo"):
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                text = f.read()
            t_match = re.search(r"^MemTotal:\s+(\d+)\s+kB", text, re.M)
            a_match = re.search(r"^MemAvailable:\s+(\d+)\s+kB", text, re.M)
            if t_match:
                mem["total_bytes"] = int(t_match.group(1)) * 1024
            if a_match:
                mem["available_bytes"] = int(a_match.group(1)) * 1024
            return mem
        except Exception:
            pass

    if sys.platform == "darwin":
        try:
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
            total = int(out)
            return {"total_bytes": total, "available_bytes": total}
        except Exception:
            pass

    if sys.platform == "win32":
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return {"total_bytes": int(stat.ullTotalPhys), "available_bytes": int(stat.ullAvailPhys)}
        except Exception:
            pass

    return mem


def detect_disk(path="."):
    """Detects total and free disk space in bytes."""
    try:
        usage = shutil.disk_usage(path)
        return {"total_bytes": usage.total, "free_bytes": usage.free}
    except Exception:
        return {"total_bytes": 0, "free_bytes": 0}


def detect_nvidia_gpus():
    """Detects NVIDIA GPUs via nvidia-smi."""
    gpus = []
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return gpus

    cmd = [
        nvidia_smi,
        "--query-gpu=index,name,memory.total,memory.free,driver_version,compute_cap",
        "--format=csv,noheader,nounits"
    ]
    try:
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        for line in output.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                idx, name, mem_total, mem_free, driver, cc = parts[:6]
                gpus.append({
                    "index": int(idx),
                    "name": name,
                    "vram_total_bytes": int(mem_total) * 1024 * 1024,
                    "vram_free_bytes": int(mem_free) * 1024 * 1024,
                    "driver": driver,
                    "compute_cap": cc
                })
    except Exception:
        pass
    return gpus


def detect_hf_cli():
    """Detects installed hf CLI and authentication status."""
    hf_path = shutil.which("hf")
    if not hf_path:
        return {"installed": False, "path": None, "version": None, "auth_user": None}

    version = None
    try:
        ver_out = subprocess.check_output([hf_path, "--version"], text=True, stderr=subprocess.DEVNULL).strip()
        version = ver_out.splitlines()[0] if ver_out else None
    except Exception:
        pass

    auth_user = None
    try:
        whoami = subprocess.check_output([hf_path, "auth", "whoami"], text=True, stderr=subprocess.DEVNULL).strip()
        if whoami and "Error" not in whoami:
            auth_user = whoami.splitlines()[0]
    except Exception:
        pass

    return {
        "installed": True,
        "path": hf_path,
        "version": version,
        "auth_user": auth_user
    }


def run_environment_check():
    """Runs a complete environment pre-flight diagnostic."""
    py_ver = platform.python_version()
    os_name = f"{platform.system()} {platform.release()} ({platform.machine()})"
    mem = detect_memory()
    disk = detect_disk()
    gpus = detect_nvidia_gpus()
    hf_cli = detect_hf_cli()

    # Network check to HF endpoint
    endpoint = get_hf_endpoint()
    token = get_hf_token()
    net_status = "ok"
    net_latency_ms = None
    try:
        import time
        req = urllib.request.Request(
            f"{endpoint}/api/models?limit=1",
            headers={"User-Agent": USER_AGENT}
        )
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                net_latency_ms = round((time.time() - t0) * 1000, 1)
    except Exception as e:
        net_status = f"unreachable ({e})"

    return {
        "python_version": py_ver,
        "os": os_name,
        "ram_total_gb": round(mem["total_bytes"] / GB, 2),
        "ram_available_gb": round(mem["available_bytes"] / GB, 2),
        "disk_free_gb": round(disk["free_bytes"] / GB, 2),
        "disk_total_gb": round(disk["total_bytes"] / GB, 2),
        "gpus": gpus,
        "hf_cli": hf_cli,
        "hf_endpoint": endpoint,
        "hf_authenticated": bool(token),
        "hf_network_status": net_status,
        "hf_latency_ms": net_latency_ms,
    }


# ==============================================================================
# Hugging Face API Ingestion
# ==============================================================================

def http_get_json(url, token=None, timeout=15):
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"Resource not found (HTTP 404): {url}")
        elif e.code in (401, 403):
            raise RuntimeError(f"Access denied (HTTP {e.code}). Gated/private repo? Set HF_TOKEN.")
        raise RuntimeError(f"HTTP error {e.code}: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")


def parse_hf_target(target):
    """Parses a user input string into target type and identifier."""
    target = target.strip()
    # Match collections: https://huggingface.co/collections/user/slug-id
    col_match = re.search(r"huggingface\.co/collections/([^/]+)/([^/?#]+)", target)
    if col_match:
        return "collection", f"{col_match.group(1)}/{col_match.group(2)}"

    # Match model URL: https://huggingface.co/org/repo
    url_match = re.search(r"(?:huggingface\.co|hf\.co)/([^/]+/[^/?#]+)", target)
    if url_match:
        return "model", url_match.group(1)

    # Match direct repo format: org/repo
    if re.match(r"^[^/]+/[^/]+$", target):
        return "model", target

    return "unknown", target


def fetch_model_info(repo_id, token=None):
    """Fetches comprehensive model metadata from Hugging Face API."""
    endpoint = get_hf_endpoint()
    api_url = f"{endpoint}/api/models/{repo_id}"
    data = http_get_json(api_url, token=token)

    # Fetch file tree to get exact file sizes and quantization layouts
    tree_url = f"{endpoint}/api/models/{repo_id}/tree/main?recursive=true"
    files = []
    try:
        files = http_get_json(tree_url, token=token)
    except Exception:
        pass

    # Extract sizes and formats
    total_download_bytes = 0
    safetensor_bytes = 0
    bin_bytes = 0
    gguf_files = []
    other_formats = set()

    for item in files:
        if item.get("type") != "file":
            continue
        size = item.get("size", 0)
        path = item.get("path", "")
        total_download_bytes += size

        if path.endswith(".safetensors"):
            safetensor_bytes += size
        elif path.endswith(".bin"):
            bin_bytes += size
        elif path.endswith(".gguf"):
            gguf_files.append({"path": path, "size_gb": round(size / GB, 2)})
        else:
            ext = os.path.splitext(path)[1]
            if ext:
                other_formats.add(ext)

    # Config info: attempt to load raw config.json for complete MoE and layer parameters
    config = data.get("config", {})
    raw_config_url = f"{endpoint}/{repo_id}/raw/main/config.json"
    try:
        raw_cfg = http_get_json(raw_config_url, token=token, timeout=5)
        if isinstance(raw_cfg, dict):
            config = {**config, **raw_cfg}
    except Exception:
        pass

    model_type = config.get("model_type", "").lower()
    architectures = [a.lower() for a in config.get("architectures", [])]

    # Determine if MoE
    num_experts = (
        config.get("num_local_experts") or 
        config.get("n_routed_experts") or 
        config.get("num_experts") or
        config.get("n_shared_experts")
    )
    active_experts = (
        config.get("num_experts_per_tok") or 
        config.get("n_active_experts") or
        config.get("num_activated_experts")
    )

    # Parameter count estimation
    safetensors_meta = (data.get("safetensors") or {}).get("total")
    params = safetensors_meta or 0

    return {
        "repo_id": repo_id,
        "author": data.get("author", repo_id.split("/")[0]),
        "id": data.get("id", repo_id),
        "private": data.get("private", False),
        "gated": data.get("gated", False),
        "downloads": data.get("downloads", 0),
        "likes": data.get("likes", 0),
        "pipeline_tag": data.get("pipeline_tag", ""),
        "model_type": model_type,
        "architectures": architectures,
        "is_moe": bool(num_experts and num_experts > 1),
        "num_experts": num_experts,
        "active_experts": active_experts,
        "params": params,
        "total_download_gb": round(total_download_bytes / GB, 2),
        "safetensor_gb": round(safetensor_bytes / GB, 2),
        "bin_gb": round(bin_bytes / GB, 2),
        "gguf_files": gguf_files,
        "tags": data.get("tags", []),
        "config": config,
    }


def fetch_collection_models(collection_slug, token=None):
    """Fetches all models in a Hugging Face collection."""
    endpoint = get_hf_endpoint()
    api_url = f"{endpoint}/api/collections/{collection_slug}"
    data = http_get_json(api_url, token=token)
    models = []
    for item in data.get("items", []):
        if item.get("type") == "model" or item.get("repoType") == "model" or item.get("item_type") == "model":
            m_id = item.get("id")
            if m_id:
                models.append(m_id)
    return {
        "collection": collection_slug,
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "model_ids": models
    }


# ==============================================================================
# Hardware & Colibri Fit Evaluation
# ==============================================================================

def assess_model_fit(model_info, hw_profile):
    """Evaluates whether a model fits in hardware and determines runner compatibility."""
    ram_gb = hw_profile["ram_total_gb"]
    disk_free_gb = hw_profile["disk_free_gb"]
    gpus = hw_profile.get("gpus", [])
    total_vram_gb = round(sum(g["vram_total_bytes"] for g in gpus) / GB, 2)

    download_gb = model_info["total_download_gb"]
    selected_gguf = None
    if model_info["gguf_files"]:
        # Find representative unified GGUF (preferring Q4_K_M or Q4_0 or Q5)
        standalone = [g for g in model_info["gguf_files"] if not re.search(r"-\d{5}-of-\d{5}\.gguf$", g["path"])]
        candidates = standalone if standalone else model_info["gguf_files"]
        
        pref = ["*q4_k_m.gguf", "*q4_0.gguf", "*q5_k_m.gguf", "*q8_0.gguf", "*.gguf"]
        for p in pref:
            matches = [g for g in candidates if fnmatch.fnmatch(g["path"].lower(), p)]
            if matches:
                selected_gguf = matches[0]
                download_gb = selected_gguf["size_gb"]
                break
        if not selected_gguf and candidates:
            selected_gguf = candidates[0]
            download_gb = selected_gguf["size_gb"]

    # 1. Check Colibri Family Mapping
    colibri_family = None
    colibri_notes = ""
    for fam_name, info in COLIBRI_FAMILIES.items():
        # Check model_type
        if model_info["model_type"] in info["model_types"]:
            colibri_family = fam_name
            colibri_notes = info["notes"]
            break
        # Check architectures
        if any(any(fnmatch.fnmatch(arch, pat) for pat in info["patterns"]) for arch in model_info["architectures"]):
            colibri_family = fam_name
            colibri_notes = info["notes"]
            break
        # Check repo name pattern
        repo_lower = model_info["repo_id"].lower()
        if any(fnmatch.fnmatch(repo_lower, pat) for pat in info["patterns"]):
            colibri_family = fam_name
            colibri_notes = info["notes"]
            break

    # 2. Memory Requirements Estimation
    # Weight memory:
    # Int4 = ~0.55 GB / billion params
    # FP8  = ~1.0 GB / billion params
    # BF16 = ~2.0 GB / billion params
    is_moe = model_info["is_moe"]
    is_gguf = bool(model_info["gguf_files"])

    # Estimate required RAM for full load vs MoE streaming
    if is_moe and colibri_family:
        dense_est_gb = max(3.5, round(download_gb * 0.15, 1))
        # Small MoE models (<35 GB) can fit entirely in RAM if system RAM is sufficient
        can_fit_all_in_ram = (download_gb <= 35.0) and (ram_gb >= download_gb * 1.15)
        if can_fit_all_in_ram:
            ram_needed_min = round(dense_est_gb + 4.0, 1)
            ram_needed_good = round(download_gb * 0.95, 1)
            mode = "from RAM (entire model cached) or streaming SSD"
        else:
            ram_needed_min = round(dense_est_gb + 4.0, 1)
            ram_needed_good = round(dense_est_gb + 12.0, 1)
            mode = "streams experts from SSD (Colibri MoE)"
    else:
        # Full model in RAM/VRAM
        ram_needed_min = max(2.0, round(download_gb * 0.9, 1))
        ram_needed_good = max(4.0, round(download_gb * 1.15, 1))
        mode = "from RAM / VRAM"

    # 3. Fit Determination
    disk_fits = disk_free_gb >= (download_gb * 1.05 + 2.0)
    ram_fits = ram_gb >= ram_needed_min
    vram_fits = total_vram_gb >= ram_needed_good if total_vram_gb > 0 else False

    status = "PASS"
    reasons = []

    if not disk_fits:
        status = "NEEDS_DISK"
        reasons.append(f"Requires ~{round(download_gb * 1.05 + 2, 1)} GB free disk; {disk_free_gb} GB free.")
    if not ram_fits:
        status = "NEEDS_RAM"
        reasons.append(f"Requires at least {ram_needed_min} GB RAM; system has {ram_gb} GB.")
    elif ram_gb < ram_needed_good:
        if status == "PASS":
            status = "TIGHT"
        reasons.append(f"RAM is tight: minimum {ram_needed_min} GB met, recommended {ram_needed_good} GB.")

    if status == "PASS":
        if is_moe and colibri_family:
            if can_fit_all_in_ram:
                reasons.append(f"Model ({download_gb} GB) fits entirely in RAM ({ram_gb} GB total), or can stream experts with {ram_needed_min} GB minimum.")
            else:
                reasons.append(f"Dense layers (~{dense_est_gb} GB) fit in RAM; experts stream from storage.")
        else:
            reasons.append(f"Entire model (~{download_gb} GB) fits comfortably in memory.")

    # 4. Actionable Recommendations
    recommended_commands = []
    hf_cli = hw_profile.get("hf_cli", {})
    has_hf = hf_cli.get("installed", False)
    repo_id = model_info["repo_id"]
    slug = repo_id.split("/")[-1]
    target_dir = f"~/models/{slug}"

    if model_info.get("gated") and not (hf_cli.get("auth_user") or hw_profile.get("hf_authenticated")):
        reasons.append("Model is gated. Authenticate with 'hf auth login' or export HF_TOKEN to access.")

    if colibri_family:
        if is_gguf and selected_gguf:
            if has_hf:
                recommended_commands.append(f"hf download {repo_id} {selected_gguf['path']} --local-dir {target_dir}")
                recommended_commands.append(f"python3 c/coli import {target_dir}/{selected_gguf['path']}")
            else:
                recommended_commands.append(f"python3 c/coli import <downloaded-file.gguf>")
        elif "int4" in repo_id.lower() or "colibri" in repo_id.lower():
            if has_hf:
                recommended_commands.append(f"hf download {repo_id} --local-dir {target_dir}")
                recommended_commands.append(f"python3 c/coli setup --model-dir {target_dir}")
            else:
                recommended_commands.append(f"python3 c/coli setup --model-dir <download-dir>")
        else:
            recommended_commands.append(f"python3 c/coli convert --repo {repo_id} --model {target_dir}")
    elif is_gguf and selected_gguf:
        if has_hf:
            recommended_commands.append(f"hf download {repo_id} {selected_gguf['path']} --local-dir {target_dir}")
            recommended_commands.append(f"python3 c/coli import {target_dir}/{selected_gguf['path']}")
            recommended_commands.append(f"llama-server -m {target_dir}/{selected_gguf['path']}")
        else:
            recommended_commands.append(f"python3 c/coli import <downloaded-file.gguf>")
            recommended_commands.append(f"llama-server -m <downloaded-file.gguf>")
    else:
        if has_hf:
            recommended_commands.append(f"hf download {repo_id} --local-dir {target_dir}")
            recommended_commands.append(f"vllm serve {target_dir}")
        else:
            recommended_commands.append(f"vllm serve {repo_id}")

    return {
        "status": status,
        "fits": status in ("PASS", "TIGHT"),
        "execution_mode": mode,
        "colibri_supported": colibri_family is not None or is_gguf,
        "colibri_family": colibri_family,
        "colibri_notes": colibri_notes,
        "selected_gguf": selected_gguf,
        "download_size_gb": download_gb,
        "ram_required_min_gb": ram_needed_min,
        "ram_required_good_gb": ram_needed_good,
        "vram_available_gb": total_vram_gb,
        "reasons": reasons,
        "recommended_commands": recommended_commands
    }


# ==============================================================================
# CLI Formatting & Presentation
# ==============================================================================

def print_env_table(env):
    print("=" * 72)
    print("  HOST ENVIRONMENT DIAGNOSTIC")
    print("=" * 72)
    print(f"  Python Version      : {env['python_version']}")
    print(f"  Operating System    : {env['os']}")
    print(f"  Host RAM (Total/Avail) : {env['ram_total_gb']} GB / {env['ram_available_gb']} GB")
    print(f"  Disk Space (Free/Total): {env['disk_free_gb']} GB / {env['disk_total_gb']} GB")
    if env["gpus"]:
        for g in env["gpus"]:
            vram_gb = round(g['vram_total_bytes'] / GB, 1)
            print(f"  NVIDIA GPU [{g['index']}]      : {g['name']} ({vram_gb} GB VRAM, sm_{g['compute_cap']}, Driver {g['driver']})")
    else:
        print("  NVIDIA GPU          : None detected (CPU execution only)")
    hf_cli = env.get("hf_cli", {})
    if hf_cli.get("installed"):
        user_info = f" (Authenticated as {hf_cli['auth_user']})" if hf_cli.get("auth_user") else " (Unauthenticated)"
        print(f"  Hugging Face CLI    : hf v{hf_cli.get('version')} at {hf_cli.get('path')}{user_info}")
    else:
        print("  Hugging Face CLI    : Not installed (optional, use 'hf' for downloading)")
    auth_str = "Authenticated (Token detected)" if env["hf_authenticated"] else "Public / Unauthenticated"
    lat_str = f"{env['hf_latency_ms']} ms" if env['hf_latency_ms'] else "N/A"
    print(f"  HF API Reachability : {env['hf_network_status']} (Latency: {lat_str})")
    print(f"  HF Auth Status      : {auth_str}")
    print("=" * 72 + "\n")


def print_evaluation_report(model_info, assessment):
    verdict = assessment["status"]
    color_sym = "✓" if verdict == "PASS" else ("!" if verdict == "TIGHT" else "✗")

    print("-" * 72)
    print(f"  MODEL: {model_info['repo_id']}")
    print("-" * 72)
    print(f"  Architecture        : {model_info['model_type'] or 'N/A'} (MoE: {'Yes' if model_info['is_moe'] else 'Dense'})")
    if model_info["is_moe"]:
        print(f"  Experts Configuration: {model_info['num_experts']} total / {model_info['active_experts']} active per token")
    print(f"  Download Size       : ~{assessment['download_size_gb']} GB" + (f" (Selected GGUF: {assessment['selected_gguf']['path']})" if assessment.get('selected_gguf') else ""))
    if model_info.get("gguf_files"):
        quants = [f"{g['path']} ({g['size_gb']} GB)" for g in model_info['gguf_files'][:4]]
        print(f"  Available GGUFs     : {len(model_info['gguf_files'])} files detected (e.g., {', '.join(quants)})")
    print(f"  RAM Requirement     : {assessment['ram_required_min_gb']} GB (min) / {assessment['ram_required_good_gb']} GB (optimal)")
    print(f"  Execution Mode      : {assessment['execution_mode']}")
    colibri_desc = f"Supported ({assessment['colibri_family']})" if assessment['colibri_family'] else ("GGUF Compatible" if model_info["gguf_files"] else "Not native (Use vLLM/llama.cpp)")
    print(f"  Colibri Native      : {colibri_desc}")
    if assessment["colibri_notes"]:
        print(f"  Colibri Note        : {assessment['colibri_notes']}")

    print(f"\n  [VERDICT] {color_sym} {verdict}")
    for r in assessment["reasons"]:
        print(f"    • {r}")

    if assessment["recommended_commands"]:
        print("\n  Recommended Next Commands:")
        for cmd in assessment["recommended_commands"]:
            print(f"    $ {cmd}")
    print("-" * 72 + "\n")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Hugging Face models or collections against local hardware and Colibri."
    )
    parser.add_argument("target", nargs="?", default=None,
                        help="Hugging Face model ID/URL or collection URL (e.g., Qwen/Qwen2.5-Coder-32B)")
    parser.add_argument("--check-env", "--doctor", action="store_true",
                        help="Run environment and pre-flight diagnostics")
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON output")
    parser.add_argument("--ram", type=float, default=None,
                        help="Override detected system RAM in GB")
    parser.add_argument("--disk", type=float, default=None,
                        help="Override detected free disk in GB")
    parser.add_argument("--vram", type=float, default=None,
                        help="Override detected GPU VRAM in GB")

    args = parser.parse_args()

    # 1. Environment Diagnostics
    env = run_environment_check()
    if args.ram:
        env["ram_total_gb"] = args.ram
    if args.disk:
        env["disk_free_gb"] = args.disk
    if args.vram and env["gpus"]:
        env["gpus"][0]["vram_total_bytes"] = int(args.vram * GB)

    if args.check_env or not args.target:
        if args.json:
            print(json.dumps({"environment": env}, indent=2))
        else:
            print_env_table(env)
            if not args.target:
                print("Usage: check_hf_model.py <model-url-or-repo-or-collection> [--json]")
        return 0

    token = get_hf_token()
    target_type, identifier = parse_hf_target(args.target)

    if target_type == "unknown":
        print(f"Error: Could not parse target {args.target!r}. Provide org/repo or huggingface.co URL.", file=sys.stderr)
        return 1

    try:
        if target_type == "collection":
            collection_info = fetch_collection_models(identifier, token=token)
            results = []
            if not args.json:
                print(f"\nEvaluating Hugging Face Collection: {collection_info['title'] or identifier}")
                print(f"Found {len(collection_info['model_ids'])} model(s).\n")

            for m_id in collection_info["model_ids"]:
                try:
                    m_info = fetch_model_info(m_id, token=token)
                    assessment = assess_model_fit(m_info, env)
                    results.append({"model": m_info, "assessment": assessment})
                    if not args.json:
                        print_evaluation_report(m_info, assessment)
                except Exception as e:
                    results.append({"model_id": m_id, "error": str(e)})
                    if not args.json:
                        print(f"  [ERROR] {m_id}: {e}\n")

            if args.json:
                print(json.dumps({"collection": collection_info, "environment": env, "evaluations": results}, indent=2))

        else:  # single model
            m_info = fetch_model_info(identifier, token=token)
            assessment = assess_model_fit(m_info, env)

            if args.json:
                print(json.dumps({"environment": env, "model": m_info, "assessment": assessment}, indent=2))
            else:
                print_env_table(env)
                print_evaluation_report(m_info, assessment)

        return 0

    except Exception as e:
        if args.json:
            print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        else:
            print(f"\n[ERROR] Evaluation failed: {e}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
