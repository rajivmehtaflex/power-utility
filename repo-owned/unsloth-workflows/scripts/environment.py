"""Linux/NVIDIA inspection and project environment setup."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run(argv: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(argv, text=True, capture_output=True, check=False)
    except OSError as exc:
        return 127, str(exc)
    return result.returncode, (result.stdout or result.stderr).strip()


def doctor(project: Path) -> dict[str, Any]:
    code, gpu_text = _run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
    return {
        "platform": sys.platform,
        "system": platform.system(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "project": str(project),
        "environment": str(project / ".unsloth" / "venv"),
        "uv": shutil.which("uv"),
        "nvidia_smi": shutil.which("nvidia-smi"),
        "gpu_available": code == 0 and bool(gpu_text),
        "gpu": gpu_text.splitlines() if gpu_text else [],
        "supported_platform": sys.platform.startswith("linux"),
        "notes": [] if sys.platform.startswith("linux") else ["training execution requires Linux/NVIDIA"],
    }


def environment_health(python: Path) -> dict[str, Any]:
    if not python.is_file():
        return {"healthy": False, "error": f"managed Python is missing: {python}"}
    probe = (
        "import importlib.metadata as m, json, sys, torch, unsloth; "
        "assert torch.cuda.is_available(), 'CUDA is unavailable'; "
        "value = (torch.ones(1, device='cuda') + 1).item(); "
        "print('UNSLOTH_HEALTH=' + json.dumps({'python': sys.version.split()[0], 'pip': m.version('pip'), "
        "'unsloth': m.version('unsloth'), 'torch': torch.__version__, 'cuda': torch.version.cuda, "
        "'device_count': torch.cuda.device_count(), 'probe': value}))"
    )
    code, output = _run([str(python), "-c", probe])
    if code != 0:
        return {"healthy": False, "error": output or "environment probe failed"}
    check_code, check_output = _run([str(python), "-m", "pip", "check"])
    if check_code != 0:
        return {"healthy": False, "error": check_output or "pip dependency check failed"}
    try:
        payload = next(line.removeprefix("UNSLOTH_HEALTH=") for line in output.splitlines() if line.startswith("UNSLOTH_HEALTH="))
        details = json.loads(payload)
    except (StopIteration, json.JSONDecodeError):
        return {"healthy": False, "error": f"invalid environment probe output: {output}"}
    return {"healthy": True, "details": details}


def setup_plan(project: Path) -> dict[str, Any]:
    env = project / ".unsloth" / "venv"
    python = env / "bin" / "python"
    uv = shutil.which("uv") or str(project / ".unsloth" / "bootstrap" / "bin" / "uv")
    return {
        "project": str(project),
        "environment": str(env),
        "python": str(python),
        "uv": uv,
        "commands": [
            [sys.executable, "-m", "venv", str(project / ".unsloth" / "bootstrap")],
            [str(project / ".unsloth" / "bootstrap" / "bin" / "python"), "-m", "pip", "install", "uv"],
            [uv, "venv", str(env), "--python", "3.12"],
            [uv, "pip", "install", "--python", str(python), "unsloth", "--torch-backend=auto"],
        ],
    }


def setup(project: Path, dry_run: bool = False) -> dict[str, Any]:
    if dry_run:
        # Dry-run is read-only and host-independent: it must not require Linux,
        # NVIDIA drivers, or a visible GPU. Execution preconditions below are
        # unchanged and still gate every non-dry-run path.
        plan = setup_plan(project)
        return {
            "dry_run": True,
            "supported_platform": sys.platform.startswith("linux"),
            **({} if sys.platform.startswith("linux") else
               {"error": "execution setup requires Linux with NVIDIA drivers"}),
            **plan,
        }
    if not sys.platform.startswith("linux"):
        raise RuntimeError("Unsloth execution setup requires Linux with NVIDIA drivers")
    gpu = doctor(project)
    if not gpu.get("gpu_available"):
        detail = "; ".join(gpu.get("gpu") or [])
        raise RuntimeError(f"NVIDIA GPU is required before setup{': ' + detail if detail else ''}")
    plan = setup_plan(project)
    if dry_run:
        return {"dry_run": True, **plan}
    project.joinpath(".unsloth").mkdir(parents=True, exist_ok=True)
    bootstrap = project / ".unsloth" / "bootstrap"
    env = project / ".unsloth" / "venv"
    if not shutil.which("uv"):
        if not (bootstrap / "bin" / "uv").exists():
            subprocess.run([sys.executable, "-m", "venv", str(bootstrap)], check=True)
            subprocess.run([str(bootstrap / "bin" / "python"), "-m", "pip", "install", "uv"], check=True)
        uv = str(bootstrap / "bin" / "uv")
    else:
        uv = shutil.which("uv") or "uv"
    if not env.exists():
        subprocess.run([uv, "venv", str(env), "--python", "3.12"], check=True)
    python = env / "bin" / "python"
    if not python.is_file():
        raise RuntimeError(f"managed environment is incomplete: {python}; repair or remove .unsloth/venv manually")
    marker = project / ".unsloth" / "install.json"
    health = environment_health(python)
    reused = health["healthy"]
    if not health["healthy"]:
        subprocess.run([uv, "pip", "install", "--python", str(python), "unsloth", "--torch-backend=auto"], check=True)
        health = environment_health(python)
    if not health["healthy"]:
        raise RuntimeError(f"managed environment failed verification: {health['error']}")
    marker.write_text(
        json.dumps({"python": str(python), "uv": uv, "environment": health["details"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "dry_run": False, **plan, "installed": True, "reused": reused,
        "marker": str(marker), "environment": health["details"],
    }
