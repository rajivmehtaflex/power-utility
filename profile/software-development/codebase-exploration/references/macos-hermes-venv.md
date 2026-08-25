# macOS Hermes venv pitfall — `dataclass slots` / `No module named pip`

Encountered 2026-08-13 while running `data-to-okf` generation inside `pi-mcp-adapter` on macOS (Hermes Desktop, Apple Silicon, Node v22).

## Symptoms
- `python3 -m venv .okf-venv && .okf-venv/bin/python -m pip install ...` fails:
  - `TypeError: dataclass() got an unexpected keyword argument 'slots'` (Hermes app leaks its 3.11 `PYTHONPATH` into project venvs, breaking C-extension wheels)
  - or `No module named pip` after `ensurepip` with system 3.9 (pip lands in `.okf-venv/usr/local/bin`, not `.okf-venv/bin`)

## Verified fix — isolated `uv` venv with clean env
```bash
# 1. Remove broken venv
rm -rf .okf-venv
# 2. Create isolated venv via uv with Homebrew Python 3.14 (bypasses Hermes 3.11 leakage)
 /opt/homebrew/bin/uv venv /tmp/<project>-okf-venv --python /opt/homebrew/bin/python3
 /opt/homebrew/bin/uv pip install --python /tmp/<project>-okf-venv/bin/python python-docx openpyxl pyyaml pypdf
# 3. Verify
 /tmp/<project>-okf-venv/bin/python -c "import docx, openpyxl, yaml, pypdf; print('OKF_DEPENDENCIES_READY')"
# 4. Run both scripts with that interpreter
 /tmp/<project>-okf-venv/bin/python /Users/rajivmehtapy/.hermes/skills/data-to-okf/scripts/generate_okf_bundle.py --source "$PWD" --dest "$PWD/../<project>-okf"
 /tmp/<project>-okf-venv/bin/python /Users/rajivmehtapy/.hermes/skills/data-to-okf/scripts/validate_okf_bundle.py "$PWD/../<project>-okf"
```

## Alternative clean-env invocation (when `uv` unavailable)
```bash
env -i HOME="$HOME" PATH="$PWD/.okf-venv/bin:/opt/homebrew/bin:/usr/bin:/bin" .okf-venv/bin/python -m pip install --quiet python-docx openpyxl pyyaml pypdf
```

## When to apply
Any time `data-to-okf` step 2 fails inside Hermes on macOS. Do not re-implement extraction — use the bundled scripts with the isolated interpreter.
