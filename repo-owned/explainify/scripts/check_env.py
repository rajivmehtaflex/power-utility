#!/usr/bin/env python3
"""Read-only runtime preflight for the explainify skill.

The two v0.1 formats have different runtime needs:

- ``asd-ste100`` (STE-inspired writing) has no tool prerequisites. This
  branch runs no external commands and always exits 0; file access itself
  is an agent-side capability a script cannot certify.
- ``explainer-video`` probes the local runtime read-only: ``uv`` on PATH,
  a Python 3.11+ interpreter discoverable through uv, ``ffmpeg``, ``ffprobe``,
  and an H.264-capable encoder in the ffmpeg build.

Every probe is a short read-only subprocess launched without a shell. This
script never installs anything, never downloads anything, and never writes
anywhere. Tool permissions, web retrieval, and image inspection remain
agent-side capability checks; this script cannot certify them.

CLI:
    check_env.py [--format {asd-ste100,explainer-video}] [--json]

``--format`` defaults to ``asd-ste100`` when omitted. ``--json`` appends a
machine-readable object (``{"format", "checks", "pass"}``) after the human
output. Exit codes: 0 = preflight passes, 1 = prerequisites missing,
2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys

PROBE_TIMEOUT_SECONDS = 15.0
FORMATS = ("asd-ste100", "explainer-video")
UV_INSTALL_URL = "https://docs.astral.sh/uv/getting-started/installation/"
FFMPEG_DOWNLOAD_URL = "https://ffmpeg.org/download.html"

# Encoder-list lines after the dashed header, e.g. " V....D libx264  description".
_ENCODER_LINE = re.compile(r"^\s*[VASFXBD.]{5,7}\s+(\S+)")


def _probe(argv: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run one read-only command without a shell; None on launch failure or timeout."""
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _first_line(text: str) -> str:
    stripped = text.strip()
    return stripped.splitlines()[0].strip() if stripped else ""


def _os_name() -> str:
    system = platform.system()
    return "macOS" if system == "Darwin" else (system or "unknown")


def _uv_hint() -> str:
    name = _os_name()
    if name == "macOS":
        return f"install with: brew install uv (macOS), or see {UV_INSTALL_URL}"
    if name == "Linux":
        return (
            "install with: apt-get install uv (Debian/Ubuntu) or dnf install uv (Fedora/RHEL), "
            f"or the standalone installer at {UV_INSTALL_URL}"
        )
    return f"install from {UV_INSTALL_URL}"


def _ffmpeg_hint() -> str:
    name = _os_name()
    if name == "macOS":
        return f"install with: brew install ffmpeg (macOS), or see {FFMPEG_DOWNLOAD_URL}"
    if name == "Linux":
        return (
            "install with: apt-get install ffmpeg (Debian/Ubuntu) or dnf install ffmpeg "
            f"(Fedora/RHEL), or see {FFMPEG_DOWNLOAD_URL}"
        )
    return f"get a full build with an H.264 encoder from {FFMPEG_DOWNLOAD_URL}"


def _check(name: str, ok: bool, detail: str) -> dict:
    return {"name": name, "ok": ok, "detail": detail}


def check_uv() -> dict:
    path = shutil.which("uv")
    if path is None:
        return _check("uv", False, _uv_hint())
    result = _probe([path, "--version"])
    if result is None:
        return _check("uv", False, f"'uv --version' timed out or failed to launch; {_uv_hint()}")
    line = _first_line(result.stdout or result.stderr)
    if result.returncode != 0 or not line:
        return _check("uv", False, f"found at {path}, but 'uv --version' failed; {_uv_hint()}")
    match = re.search(r"uv\s+(\S+)", line)
    version = match.group(1) if match else line
    return _check("uv", True, f"{version} ({path})")


def check_python(uv_path: str | None) -> dict:
    name = "python-3.11+-via-uv"
    if uv_path is None:
        return _check(name, False, f"not checked: uv is missing; {_uv_hint()}")
    # Read-only discovery probe: 'uv python find' locates an installed
    # interpreter and never installs or downloads one.
    result = _probe([uv_path, "python", "find", "3.11"])
    if result is None:
        return _check(
            name,
            False,
            "'uv python find 3.11' timed out or failed to launch; "
            "install with: uv python install 3.11 (suggested only; never run by this script)",
        )
    interpreter = _first_line(result.stdout)
    if result.returncode != 0 or not interpreter:
        return _check(
            name,
            False,
            "no installed Python 3.11 interpreter found via 'uv python find 3.11'; "
            "install with: uv python install 3.11 (suggested only; never run by this script)",
        )
    return _check(name, True, interpreter)


def check_ffmpeg() -> dict:
    path = shutil.which("ffmpeg")
    if path is None:
        return _check("ffmpeg", False, _ffmpeg_hint())
    result = _probe([path, "-version"])
    if result is None:
        return _check("ffmpeg", False, f"'ffmpeg -version' timed out or failed to launch; {_ffmpeg_hint()}")
    line = _first_line(result.stdout or result.stderr)
    if result.returncode != 0 or not line:
        return _check("ffmpeg", False, f"found at {path}, but 'ffmpeg -version' failed; {_ffmpeg_hint()}")
    match = re.search(r"ffmpeg version\s+(\S+)", line)
    version = match.group(1) if match else line
    return _check("ffmpeg", True, f"{version} ({path})")


def check_ffprobe() -> dict:
    path = shutil.which("ffprobe")
    if path is None:
        return _check("ffprobe", False, f"the ffmpeg package provides ffprobe; {_ffmpeg_hint()}")
    return _check("ffprobe", True, f"({path})")


def _parse_encoder_names(encoder_text: str) -> list[str]:
    names: list[str] = []
    past_header = False
    for line in encoder_text.splitlines():
        stripped = line.strip()
        if not past_header:
            if re.fullmatch(r"-{3,}", stripped):
                past_header = True
            continue
        match = _ENCODER_LINE.match(line)
        if match:
            names.append(match.group(1))
    return names


def _is_h264_encoder(name: str) -> bool:
    return name in ("libx264", "h264_videotoolbox") or "h264" in name.lower()


def check_h264() -> dict:
    name = "h264-encoder"
    path = shutil.which("ffmpeg")
    if path is None:
        return _check(name, False, f"not checked: ffmpeg is missing; {_ffmpeg_hint()}")
    result = _probe([path, "-hide_banner", "-encoders"])
    if result is None or result.returncode != 0:
        return _check(name, False, f"'ffmpeg -hide_banner -encoders' failed or timed out; {_ffmpeg_hint()}")
    matched = [encoder for encoder in _parse_encoder_names(result.stdout or "") if _is_h264_encoder(encoder)]
    if not matched:
        return _check(
            name,
            False,
            "this ffmpeg build exposes no H.264 encoder (libx264 or another h264 encoder); "
            f"use a full ffmpeg build; {_ffmpeg_hint()}",
        )
    return _check(name, True, "available: " + ", ".join(matched))


def run_checks(fmt: str) -> list[dict]:
    if fmt == "asd-ste100":
        return [
            _check(
                "asd-ste100",
                True,
                "writing has no tool prerequisites; file access is an agent-side "
                "capability this script cannot certify",
            )
        ]
    uv_path = shutil.which("uv")
    return [check_uv(), check_python(uv_path), check_ffmpeg(), check_ffprobe(), check_h264()]


def _render_line(check: dict) -> str:
    if check["ok"]:
        return f"[ok] {check['name']} {check['detail']}".rstrip()
    return f"[missing] {check['name']} — {check['detail']}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_env.py",
        description=(
            "Read-only explainify runtime preflight. Never installs, downloads, or writes anything; "
            "probes commands with short timeouts only."
        ),
    )
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default=None,
        help="format to preflight (default: asd-ste100, which has no tool prerequisites)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="also print a machine-readable JSON object after the human output",
    )
    args = parser.parse_args(argv)

    fmt = args.format or "asd-ste100"
    if args.format is None:
        print("format not specified; defaulting to asd-ste100 (writing has no tool prerequisites)")
        print()

    checks = run_checks(fmt)
    for check in checks:
        print(_render_line(check))
    missing = sum(1 for check in checks if not check["ok"])
    print()
    verdict = "PASS" if missing == 0 else f"FAIL ({missing} missing)"
    print(f"preflight: {verdict}")
    print("note: image inspection and web retrieval are agent-side capabilities this script cannot certify.")
    if fmt == "explainer-video":
        print("note: command-execution permission is also agent-side; passing probes do not certify it.")
    if args.json:
        print(json.dumps({"format": fmt, "checks": checks, "pass": missing == 0}, indent=2))
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
