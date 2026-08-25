---
name: python-version-management
description: Force Python versions via uv for cloud compatibility.
license: MIT
metadata:
  author: Hermes Agent
  hermes_tags: python, uv, venv, compatibility, devops, cloud-deploy
  platforms: linux, macos, windows
  version: 1.0.0
---

# Python Version Management (uv)

Use this skill when a project requires a specific Python version (e.g., for cloud provider compatibility or specific library requirements) that differs from the system default or the version `uv` automatically selects.

## Workflow: Forcing a Specific Version

When you encounter a "Unsupported Python version" error (common in cloud image builders) or need to pin a version:

1. **Install the target version:**
   ```bash
   uv python install 3.12
   ```

2. **Pin and recreate the virtual environment on that version:**
   `uv python install` alone does **not** recreate an existing venv — verified 2026-08-12, Modal kept failing with `Unsupported Python version: '3.13'` after `uv sync` until the venv was recreated. Prefer `uv python pin` (writes `.python-version` so every later `uv sync` respects it), then recreate:
   ```bash
   uv python pin 3.12
   rm -rf .venv && uv sync
   # — or without a pin file —
   uv venv --python 3.12 --clear && uv sync
   ```
   The `rm -rf .venv` / `--clear` step is mandatory when downgrading; `uv sync` alone reuses the old interpreter.

3. **Verify the active version before any mutating command:**
   ```bash
   .venv/bin/python --version
   .venv/bin/modal --version   # or .venv/bin/<command> --version
   ```
   Also verify with a sanitized env when running from Hermes (see Sanitizing the Environment below). Full transcript: `references/modal-python313-modal-deploy-2026-08-12.md`.

## Compatibility Pitfalls

| Platform/Tool | Version Constraint | Symptom | Fix |
|-----------|--------------------|----------|---|
| **Modal Image Builder** | Max 3.12 (Image 2023.12) | `Unsupported Python version: '3.13'` | `uv python pin 3.12 && rm -rf .venv && uv sync` — `uv python install` alone does NOT recreate venv |
| **Old Legacy Projects** | Max 3.9 | `SyntaxError` or `ImportError` | Force 3.9 |
| **C-Extension Wheels** | Must match venv | `ModuleNotFoundError` (e.g. `watchfiles._rust_notify`) | Ensure venv Python version matches the wheels in `site-packages` |

## Tooling Patterns

### Sanitizing the Environment
When running tools from a venv inside an agent's terminal, inherited `PYTHONPATH` can leak site-packages from the agent's own runtime (e.g., Python 3.11) into the project's venv (e.g., Python 3.12), causing binary crashes.

**The Fix:** Prefer the project's venv executable, then remove inherited Python overrides before invoking it. Use the minimal `env -i` form when you need a fully isolated process; `env -u` is a lighter option when the normal shell environment is otherwise required.
```bash
# Verify the project interpreter and CLI first
.venv/bin/python --version
.venv/bin/<command> --version

# Lightweight isolation
env -u PYTHONPATH -u PYTHONHOME .venv/bin/<command> <args>

# Full isolation
env -i HOME="$HOME" PATH="$PWD/.venv/bin:/usr/bin:/bin:/usr/local/bin" .venv/bin/<command> <args>
```

Never rely on a globally installed launcher when a project venv is present: the launcher may select an older system interpreter or inherit incompatible agent packages. Run a harmless `--version`/status check before any mutating command such as deploy, migrate, or publish. When downgrading, always verify `.venv/bin/python --version` changed — `uv sync` after `uv python install` silently reuses the old venv (2026-08-12 Modal case).

### Verifying Allocation vs. Reporting
Inside slim containers (e.g., `debian_slim`), tools like `free -h` are missing. Cgroup reporting for memory often shows the host total rather than the container limit.
- **Reliable check:** Use `nproc` to verify CPU core allocation.
- **Unreliable check:** `/sys/fs/cgroup/memory/memory.limit_in_bytes` (often reports host total).
- **Source of Truth:** Trust the deployment config (`config.py`) and the scheduler's confirmation.
