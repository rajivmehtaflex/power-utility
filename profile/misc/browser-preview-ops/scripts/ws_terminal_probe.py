#!/usr/bin/env python3
"""
End-to-end probe for WebSocket-PTY web terminals (xterm.js frontends).

Ground-truth verification for apps like the Modal web-terminal template.
Synthetic browser typing (Hermes drive_preview/browser_type into the xterm
helper textarea) can echo text without executing, and headless canvas
screenshots render inconsistently — this probe drives the app's actual
WebSocket, exercising the real PTY in both directions.

Protocol (matches the Modal template's static/index.html + main.py):
  - connect to <base>/ws
  - on open the frontend sends a JSON text frame: {"type":"resize","rows":N,"cols":M}
  - client -> server: binary frames are written straight to the PTY
    (command bytes + b"\\r" to execute)
  - server -> client: PTY output arrives as binary frames

Usage:
  .venv/bin/python ws_terminal_probe.py <wss://host/ws> ["cmd1" "cmd2" ...]

Example:
  .venv/bin/python ws_terminal_probe.py \
    wss://rajivmehtaflex--modal-web-terminal-fastapi-app.modal.run/ws \
    "nproc" "nvidia-smi -L"

Requires aiohttp (present in Modal's dependency tree).
"""

import asyncio
import json
import sys

import aiohttp

PROMPT_HINTS = ("#", "$")


async def read_until_silence(ws, buf: bytearray, timeout: float = 20.0, quiet: float = 0.5) -> None:
    """Collect binary frames until `quiet` seconds pass without new data."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        try:
            msg = await asyncio.wait_for(ws.receive(), timeout=quiet)
        except asyncio.TimeoutError:
            return  # quiet window elapsed -> command output finished
        if msg.type == aiohttp.WSMsgType.BINARY:
            buf.extend(msg.data)
        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
            return


async def run_cmd(ws, cmd: str) -> str:
    buf = bytearray()
    await ws.send_bytes(cmd.encode() + b"\r")
    await read_until_silence(ws, buf)
    return buf.decode(errors="replace")


async def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    url = sys.argv[1]
    cmds = sys.argv[2:] or ["nproc", "nvidia-smi -L"]

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            # Mirror the frontend's on-open resize frame
            await ws.send_str(json.dumps({"type": "resize", "rows": 24, "cols": 100}))

            buf = bytearray()
            await read_until_silence(ws, buf, timeout=15.0)
            text = buf.decode(errors="replace")
            if not any(h in text for h in PROMPT_HINTS):
                print("No PTY prompt received. Raw output so far:")
                print(text[-500:])
                sys.exit(1)
            print("PROMPT OK:", text.strip().splitlines()[-1] if text.strip() else "(empty)")

            for cmd in cmds:
                print(f"\n$ {cmd}")
                print(await run_cmd(ws, cmd))

            await ws.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
