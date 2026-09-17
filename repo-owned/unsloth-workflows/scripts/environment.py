"""Linux/NVIDIA inspection and project environment setup."""

from __future__ import annotations

import json
import os
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
    if dry_run and not sys.platform.startswith("linux"):
        plan = setup_plan(project)
        return {
            "dry_run": True,
            "supported_platform": False,
            "error": "execution setup requires Linux with NVIDIA drivers",
            **plan,
        }
    if not sys.platform.startswith("linux"):
        raise RuntimeError("Unsloth execution setup requires Linux with NVIDIA drivers")
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
    marker = project / ".unsloth" / "install.json"
    if not marker.exists():
        subprocess.run([uv, "pip", "install", "--python", str(python), "unsloth", "--torch-backend=auto"], check=True)
        marker.write_text(json.dumps({"python": str(python), "uv": uv}, indent=2) + "\n", encoding="utf-8")
    return {"dry_run": False, **plan, "installed": True, "marker": str(marker)}
