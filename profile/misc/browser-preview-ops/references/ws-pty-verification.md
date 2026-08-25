# Verifying WebSocket-PTY / xterm.js Web Apps (2026-08-21 session)

## Symptom

Driving a browser terminal (Modal web-terminal template: xterm.js over a
`/ws` WebSocket to a bash PTY) with synthetic typing:

- `drive_preview` typing into the `.xterm-helper-textarea` echoed text into
  the terminal but commands did **not** execute; repeated submissions
  appeared to re-run the previous command.
- Automation browser (`browser_type` + `browser_press Enter`) echoed the
  command line at the prompt but Enter never dispatched; screenshots showed
  the echoed command with no output line.
- `browser_vision` canvas reads were unreliable (blank or partial frames).
- `read_preview` (preview pane) DID show real terminal text — the app itself
  was healthy; only synthetic keyboard events were broken.

**Takeaway:** when synthetic typing fails on a WebSocket-driven UI, the app
may be perfectly fine. Verify via the real protocol before blaming the app.

## Working verification: direct WebSocket probe

Frontend protocol (matches the Modal template's `static/index.html` + `main.py`):

- connect to `<base>/ws`
- on open, client sends a JSON text frame: `{"type":"resize","rows":N,"cols":M}`
- client→server **binary** frames are written straight to the PTY
  (`cmd.encode() + b"\r"` executes the command)
- server→client PTY output arrives as **binary** frames

Probe: `scripts/ws_terminal_probe.py` (aiohttp only — aiohttp is already in
Modal's dependency tree). Verified outputs from a 2×T4 / 8-CPU / 8GB deploy:

```
$ nproc
8
$ nvidia-smi -L
GPU 0: Tesla T4 (UUID: ...)
GPU 1: Tesla T4 (UUID: ...)
```

## One-shot allocation check (Modal)

`modal shell` accepts resource flags without a function reference:

```bash
env -i HOME="$HOME" PATH="$PWD/.venv/bin:/usr/bin:/bin" .venv/bin/modal shell \
  --gpu T4:2 --cpu 8 --memory 8192 -c "nproc && nvidia-smi -L"
```

Same allocation path as a real deploy — doubles as post-deploy verification.
Prefer one-shot `-c` probes over interactive shells in automation.
