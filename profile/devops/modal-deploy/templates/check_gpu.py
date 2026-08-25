#!/usr/bin/env python3
"""
GPU availability pre-check for Modal deployments.

Spins up a minimal container with the requested GPU via
`modal shell --gpu <MODEL> -c "nvidia-smi -L"` and reports whether the GPU
was allocated within a time budget.

Note: `modal shell` only rejects `--gpu` when combined with a *function
reference*; with no ref (as used here) it starts a fresh container with the
requested resources, so this is a genuine allocation test.

Caveat: the pre-check waits in the same allocation queue as a real deploy,
so it is timeout-bounded and optional. For high-availability GPUs (T4, A10)
you can safely skip it (`./deploy.sh` skips by default).
"""

import argparse
import os
import shutil
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()

try:
    import config
    default_gpu = config.GPU_MODEL or "T4"
except ImportError:
    default_gpu = os.getenv("MODAL_GPU_MODEL", "T4").strip().strip('"')


def suggest_alternatives(failed_gpu: str) -> list[str]:
    """Suggest alternative GPU models ordered by availability."""
    alternatives = {
        "B200": ["H100", "H200", "L40S", "A100", "A10", "L4", "T4"],
        "H200": ["H100", "L40S", "A100", "A10", "L4", "T4"],
        "H100": ["L40S", "A100", "A10", "L4", "T4"],
        "L40S": ["A100", "A10", "L4", "T4"],
        "A100": ["A10", "L4", "T4"],
        "A10":  ["L4", "T4"],
        "L4":   ["T4", "A10"],
        "T4":   ["A10", "L4", "A100"],
    }
    return alternatives.get(failed_gpu, ["T4", "A10", "L4"])


def find_modal_bin() -> str:
    """Prefer the project venv's modal CLI, fall back to PATH."""
    venv_modal = os.path.join(".venv", "bin", "modal")
    if os.path.exists(venv_modal):
        return venv_modal
    found = shutil.which("modal")
    if found:
        return found
    print("❌ modal CLI not found (.venv/bin/modal or PATH). Run: uv sync")
    sys.exit(2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Modal GPU availability")
    parser.add_argument(
        "--gpu",
        default=default_gpu,
        help="GPU model to check (default: GPU_MODEL from config.py, else T4)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Seconds to wait for GPU allocation before giving up (default: 120)",
    )
    args = parser.parse_args()

    modal_bin = find_modal_bin()

    print("=" * 60)
    print("🚀 Modal GPU Availability Checker")
    print("=" * 60)
    print(f"📋 GPU: {args.gpu}   ⏱  Timeout: {args.timeout}s")
    print("   Requesting a minimal container to test allocation...")
    print()

    try:
        result = subprocess.run(
            [modal_bin, "shell", "--gpu", args.gpu, "--cpu", "1",
             "-c", "nvidia-smi -L"],
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired:
        print(f"⏱  No {args.gpu} allocated within {args.timeout}s (queue congestion).")
        print()
        print(f"💡 {args.gpu} alternatives (ordered by availability):")
        for i, alt in enumerate(suggest_alternatives(args.gpu)[:3], 1):
            print(f"   {i}. {alt}")
        print()
        print("   Or deploy anyway and watch the logs:")
        print("     ./deploy.sh && .venv/bin/modal app logs <app-name>")
        return 1

    gpu_lines = [l for l in result.stdout.splitlines() if l.startswith("GPU ")]
    if result.returncode == 0 and gpu_lines:
        print(f"✅ {args.gpu} allocated successfully:")
        for line in gpu_lines:
            print(f"   {line}")
        return 0

    print(f"❌ GPU check failed (exit {result.returncode}).")
    tail = (result.stderr or result.stdout).strip().splitlines()[-5:]
    for line in tail:
        print(f"   {line}")
    print()
    print(f"💡 {args.gpu} alternatives (ordered by availability):")
    for i, alt in enumerate(suggest_alternatives(args.gpu)[:3], 1):
        print(f"   {i}. {alt}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
