---
name: prepare-python-folder
description: Sets up a new Python project directory using uv.
---

# prepare-python-folder

Sets up a new Python project directory using `uv`.

## Usage
Provide the desired folder path when prompted or via your own script logic.

## Steps
1. Create the directory if it does not exist.
2. Change into the directory.
3. Initialize the project: `uv init -p 3.12` (or read `.python-version` if present).
4. Sync dependencies: `uv sync`.
5. Verify: `uv run python --version` matches the pinned version.

## Script
```bash
#!/bin/bash
if [ -z "$1" ]; then
    read -p "Enter folder path: " folder_path
else
    folder_path="$1"
fi

mkdir -p "$folder_path"
cd "$folder_path" || exit
uv init -p 3.12
uv sync
uv run python --version
```

## Pitfalls (from real sessions)
- **Ensure `uv` is installed** and on PATH (`which uv` first).
- **Existing dir:** `uv init` may warn or fail in non-empty dirs — check for an existing `pyproject.toml` before initializing.
- **Cloud targets:** pin Python via `.python-version` + `[requires-python]` in pyproject.toml; some providers only offer specific versions (see `python-version-management` skill).
- **Hermes terminal PYTHONPATH leak (macOS):** Hermes exports its Python 3.11 `PYTHONPATH`, which leaks into venvs and breaks C-extension imports. Run venv commands with it cleared:
  ```bash
  env -i HOME="$HOME" PATH="$PWD/.venv/bin:/usr/bin:/bin" .venv/bin/python <script>
  ```
- **pytest projects:** configure `[tool.pytest.ini_options] pythonpath = ["."]` (or `["src"]`) in pyproject.toml — never `pip install -e`; this workspace uses uv exclusively.

## Related Skills
- `python-version-management` — forcing Python versions for cloud compatibility
- `cli-tool-installation` — installing uv itself if missing
