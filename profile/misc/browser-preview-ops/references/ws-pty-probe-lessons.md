# WS-PTY Probe Script Lessons (2026-08-24 session, `websockets` variant)

Follow-up to `ws-pty-verification.md`. A second probe implementation (using the
`websockets` package instead of aiohttp) hit three failure modes worth
pre-empting in any future WS→PTY probe:

## 1. Command echoed but never executed

Sending one big multi-line command blob often produces only terminal echo with
no output. Fix: send the command body, wait ~300ms, then send Enter (`b"\r"`)
as a SEPARATE frame — the PTY needs the newline to arrive as its own write.

```python
await ws.send(cmd_body.encode())
await asyncio.sleep(0.3)
await ws.send(b"\r")
```

## 2. Marker-count break conditions fire early

Breaking when a marker "appears twice" matches the ECHO of the marker inside
the typed command itself, exiting before execution output arrives. Fix:
fixed-time drain instead of marker counting — sleep 10–15s after sending, then
read everything available until a short recv timeout (5–8s):

```python
await asyncio.sleep(12)
out = b""
try:
    while True:
        msg = await asyncio.wait_for(ws.recv(), timeout=6)
        out += msg if isinstance(msg, bytes) else msg.encode()
except asyncio.TimeoutError:
    pass
```

## 3. Echo pollution when slicing output

`text.rfind(marker)` can land on the echo too. Slice from the first occurrence
of an output-only sentinel that is NOT part of the typed command (e.g. the
command echoes `'--- TOOLS ---'` quoted; the executed output prints
`--- TOOLS ---` bare — use find() on the exact unquoted form), or just print
the tail.

## Volume persistence proof pattern (Modal)

End-to-end proof that a Modal volume survives container restarts, all over the
WS probe channel:

1. Write a timestamped marker into the volume path (e.g.
   `/root/.agents/persist-marker.txt`) via the PTY.
2. Force-stop the container: `modal container stop <id> --yes` (non-interactive
   shells abort without `--yes`). Verify empty `modal container list`.
3. Open a NEW ws connection → fresh container boots.
4. Read the marker back. Marker survives = persistence proven.

Related Modal build gotchas verified this session: one volume cannot be
mounted at multiple paths for the same function (mount once at a parent dir +
symlink per-tool paths during image build), and `.run_commands()` after
`.add_local_dir()` requires `copy=True`.
