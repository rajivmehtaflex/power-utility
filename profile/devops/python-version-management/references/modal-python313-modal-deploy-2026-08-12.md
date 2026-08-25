# Modal Python 3.13 Deploy Failure — 2026-08-12

## Failure transcript
```
✓ Created objects.
├── 🔨 Created mount /web-terminal-modal/modal_app.py
...
╭─ Error ──────────────────────────────────────────────────────╮
│ Unsupported Python version: '3.13'. When using the '2023.12' │
│ Image builder, Modal supports the following series:           │
│ ['3.10', '3.11', '3.12'].                                    │
╰──────────────────────────────────────────────────────────────╯
```

Provider: Modal Image builder `2023.12`, series cap 3.12. Project had `requires-python = ">=3.12"` so `uv` auto-selected 3.13.14 -> `.venv` was 3.13.

## What did NOT fix it
```bash
uv python install 3.12
uv sync   # kept the existing .venv (3.13) — deploy still failed with same error
```

Evidence: `.venv/bin/python --version` still 3.13.14 after `uv sync`; `uv python list` showed 3.12 installed but not active in venv.

## What fixed it
```bash
uv python pin 3.12          # writes .python-version = 3.12 so future uv sync respects it
rm -rf .venv && uv sync     # recreate venv on 3.12
# — equivalent without a pin file: uv venv --python 3.12 --clear && uv sync
.venv/bin/python --version  # -> Python 3.12.10
env -i HOME="$HOME" PATH="$PWD/.venv/bin:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin" \
  .venv/bin/modal profile list   # verify auth (sanitized env — Hermes leaks PYTHONPATH)
env -i HOME="$HOME" PATH="$PWD/.venv/bin:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin" \
  .venv/bin/modal deploy modal_app.py  # -> App deployed in 3.395s
```

## Deployment that succeeded
- App: `web-terminal-cpu-4core` (rajivmehtaflex workspace)
- Resources: CPU=4.0, MEMORY=8192, GPU_COUNT=0 (CPU-only)
- URL: https://rajivmehtaflex--web-terminal-cpu-4core-fastapi-app.modal.run
- Dir: /Users/rajivmehtapy/Documents/Dev/Chrome_Prompt_API/web-terminal-modal
- Also required sanitized env for every `modal` call from Hermes (`watchfiles._rust_notify` leak).

## Rule for skills
When Modal reports unsupported Python, never stop at `uv python install`. Always recreate the venv (`rm -rf .venv && uv sync` or `uv venv --python X --clear`) and verify with `.venv/bin/python --version` before retrying deploy.
