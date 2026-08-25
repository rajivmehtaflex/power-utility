# api/core/hermes_bridge.py — The Core Subprocess Bridge
#
# Wraps `hermes chat -q -z` into async Python functions.
# This is the server-side equivalent of the Android Intent bridge —
# but uses subprocess.run() directly on the same machine.

import asyncio
import subprocess
import re
from typing import Optional

from api.core.config import load_config

config = load_config()


async def call_hermes(
    prompt: str,
    session_id: Optional[str] = None,
    skills: Optional[list[str]] = None,
    max_turns: Optional[int] = None,
    timeout: Optional[int] = None,
) -> dict:
    """
    Call Hermes Agent with full skill and tool support.

    Returns:
        {response, session_id, success, error}
    """
    max_turns = max_turns or config["hermes"]["max_turns"]
    timeout = timeout or config["hermes"]["timeout"]

    cmd = [
        config["hermes"]["binary"],
        "chat",
        "-q",
        "-z",
        "--max-turns", str(max_turns),
    ]

    if session_id:
        cmd.extend(["--resume", session_id])

    if skills:
        for skill in skills:
            cmd.extend(["-s", skill])

    cmd.append(prompt)

    loop = asyncio.get_event_loop()

    try:
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            ),
        )
    except subprocess.TimeoutExpired:
        return {
            "response": "",
            "session_id": session_id,
            "success": False,
            "error": f"Request timed out after {timeout}s",
        }

    if result.returncode != 0:
        return {
            "response": "",
            "session_id": session_id,
            "success": False,
            "error": result.stderr[:1000] if result.stderr else "Unknown error",
        }

    new_session_id = session_id
    if not session_id:
        new_session_id = await _get_latest_session_id()

    return {
        "response": result.stdout.strip(),
        "session_id": new_session_id,
        "success": True,
        "error": None,
    }


async def _get_latest_session_id() -> Optional[str]:
    """Extract most recent session ID from `hermes sessions list`."""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["hermes", "sessions", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            ),
        )
        for line in result.stdout.strip().split("\n"):
            match = re.search(r"(\d{8}_\d{6}_[a-f0-9]+)", line)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


async def create_named_session(name: str) -> str:
    """Create a named resumable session."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            [
                config["hermes"]["binary"],
                "chat",
                "-q",
                "-z",
                "--continue",
                name,
                "Session initialized.",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        ),
    )
    return await _get_latest_session_id()


async def list_sessions() -> list[dict]:
    """List all Hermes sessions."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            ["hermes", "sessions", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        ),
    )
    sessions = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            sessions.append({"raw": line.strip()})
    return sessions
