# Custom `modal_app.py` Mount Pattern vs Template

The `templates/modal_app.py` uses `.add_local_dir(".", remote_path="/root", ignore=[...])`, which pulls the entire project into the container — including `config.py`, `.env`, `main.py`, and `static/`. That works for a green-field terminal project.

Many existing repositories (including the root `g-llm-training-ops`) have an older/custom `modal_app.py` that mounts files individually:

```python
.add_local_file("main.py", remote_path="/root/main.py")
.add_local_dir("static", remote_path="/root/static")
```

This pattern is safer for selective uploads but has two common failure modes:

## Pitfall 1: `config.py` Not Mounted

`main.py` imports `config`. If the image does not include `config.py`, the container crashes at startup:

```
ModuleNotFoundError: No module named 'config'
```

**Fix:** Add `config.py` explicitly:

```python
.add_local_file("main.py", remote_path="/root/main.py")
.add_local_file("config.py", remote_path="/root/config.py")
.add_local_dir("static", remote_path="/root/static")
```

Or, prefer `add_local_dir(".", ...)` with a proper ignore list (`.git`, `.venv`, `__pycache__`, `docs/`, `*.md`, `.env`, `uv.lock`) — it captures all runtime files automatically.

## Pitfall 2: Missing `python-dotenv`

`main.py` uses `load_dotenv()`. The image must install `python-dotenv`:

```python
.pip_install("fastapi", "uvicorn", "python-dotenv")
```

Without it, `import load_dotenv` fails at module load time.

## Verification After Fix

After editing `modal_app.py`, verify before deploying:

```bash
# Confirm the file exists locally
cat config.py

# Confirm it is listed in the image mounts (deploy output shows it)
.venv/bin/modal deploy modal_app.py

# Confirm live response
curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
  https://rajjnd--g-llm-training-ops-terminal-fastapi-app.modal.run
```

Expected result: `200`.

## When to Prefer Individual Mounts

| Scenario | Pattern | Why |
|----------|---------|-----|
| Green-field web terminal | `.add_local_dir(".", ...)` | Simple, captures config + code + static |
| Existing repo with separate `main.py` / `static/` | `add_local_file` + `add_local_dir` | Selective uploads, avoids uploading `.git/` or `.venv/` accidentally |
| Mixed project (not a terminal) | Custom mount list | Only include files the container needs |

In all cases: **if `main.py` imports `config`, mount `config.py`. If `main.py` calls `load_dotenv()`, install `python-dotenv`.**
