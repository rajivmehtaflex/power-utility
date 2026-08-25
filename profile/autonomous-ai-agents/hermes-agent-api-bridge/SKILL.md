---
name: hermes-agent-api-bridge
description: Bridge Hermes Agent to external apps via subprocess or HTTP.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: hermes-agent, web-service-launch
  hermes_tags: hermes, api, bridge, subprocess, fastapi, ollama, integration, http
  platforms: linux, macos, windows
  version: 1.0.0
---

# Hermes Agent API Bridge

Embed Hermes Agent into external applications — ChainLit, web apps, Android clients, headless servers. Full agent loop (skills, tools, memory, sessions) accessible from any language or platform.

**Trigger:** User asks to call Hermes from Python, use Hermes in an app, build an API around Hermes, run Hermes on a server, connect a local LLM to Hermes, or integrate Hermes with ChainLit/Android/web.

## The Core Subprocess Pattern

Hermes is invoked as a subprocess via `hermes chat -q -z`:

```python
cmd = ["hermes", "chat", "-q", "-z", "--max-turns", "20"]

# Force-load specific skills
for skill in skills:
    cmd.extend(["-s", skill])

# Resume a session for stateful conversations
if session_id:
    cmd.extend(["--resume", session_id])

cmd.append(prompt)

result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
response = result.stdout.strip()
```

### Key flags

| Flag | Purpose |
|---|---|
| `-q` | Non-interactive single query |
| `-z` | **Oneshot: print ONLY final response** (no banners, spinners, tool previews — clean for parsing) |
| `--max-turns N` | Cap tool-calling iterations |
| `-s SKILL` | Preload specific skills (repeatable) |
| `--resume SESSION_ID` | Resume session by ID (stateful conversation) |
| `--continue NAME` | Resume by name |

### What `-q -z` gives you vs `hermes proxy`

| Surface | Agent Loop? | Skills? | Tools? | Session State? |
|---|---|---|---|---|
| `hermes proxy` (OpenAI-compatible) | ❌ Raw model only | ❌ | ❌ | ❌ |
| `hermes chat -q -z` | ✅ Full | ✅ Auto-match + force-load | ✅ | ✅ Via `--resume` |

**Never use `hermes proxy` when you need skills/tools/agent loop.** It's a dumb model relay.

## Session State Management

Each `hermes chat -q -z` call starts fresh by default. For stateful conversations:

```
Turn 1: hermes chat -q -z "brainstorm ideas"
    → Creates session 20260725_143052_a1b2c3
    → Capture via: hermes sessions list (parse most recent ID)

Turn 2: hermes chat -q -z --resume 20260725_143052_a1b2c3 "narrow to top 3"
    → Loads full history from state.db
    → Hermes remembers turn 1

Turn 3: hermes chat -q -z --resume 20260725_143052_a1b2c3 "implement option 2"
    → Full context of turns 1+2
```

### Extracting session ID

```python
import subprocess, re

result = subprocess.run(["hermes", "sessions", "list"],
                       capture_output=True, text=True, timeout=10)
for line in result.stdout.split("\n"):
    match = re.search(r"(\d{8}_\d{6}_[a-f0-9]+)", line)
    if match:
        return match.group(1)
```

### Per-user sessions

Map each external user to their own Hermes session:
```python
user_sessions = {}  # user_id → hermes_session_id

def handle_message(user_id, message):
    sid = user_sessions.get(user_id)
    result = call_hermes(prompt=message, session_id=sid)
    if result["success"]:
        user_sessions[user_id] = result["session_id"]
    return result["response"]
```

## HTTP API Bridge Pattern

For multi-client access, wrap the subprocess in a FastAPI server. **Full template code is in `templates/`** — the pattern is:

```
Client (any language) → POST /chat {prompt, session_id, skills}
    → FastAPI route calls hermes_bridge.call_hermes()
    → subprocess.run(["hermes", "chat", "-q", "-z", ...])
    → Returns {response, session_id, success, error}
```

Key endpoints:
- `POST /chat` — stateful chat with skill support
- `GET /sessions` / `POST /sessions/new` — session management
- `POST /files/in` — upload file for Hermes to process
- `GET /files/out/{filename}` — download generated files
- `GET /health` — check Hermes + model server status

**Authentication:** Bearer token in Authorization header.

**Copy the full FastAPI bridge from:** `templates/` (main.py, routes/, core/hermes_bridge.py, config, systemd service, Dockerfile).

## Local LLM Integration (Ollama)

Point Hermes at a local model for zero-cost, fully private operation:

```bash
# Install Ollama + pull model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3.5:14b

# Configure Hermes
hermes config set model.provider custom
hermes config set model.default qwen3.5:14b
hermes config set model.base_url http://127.0.0.1:11434/v1
```

**Critical: tool calling requires 4B+ models.** Models under 2B can't reliably emit structured function calls needed for Hermes's agent loop. See `references/local-llm-setup.md` for model sizing and benchmarks.

**Cloud fallback (optional):**
```yaml
fallback_providers:
  - provider: openrouter
    model: anthropic/claude-sonnet-4
```

## Verification Pattern

Always verify the bridge with FastAPI's TestClient — no live server needed:

```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
r = client.post("/chat", json={"prompt": "test"}, headers=AUTH)
assert r.status_code == 200
assert "success" in r.json()
```

**Full 14-test self-contained suite in `templates/test_api.py`.**

## Pitfalls

### Pitfall: Scaffolding wrong architecture before confirming target
**Symptom:** You build a full FastAPI server scaffold (37 files), then the user asks "what is the role of the Python file?" — revealing they wanted on-device Android + Termux (no Python at all).
**Root cause:** This skill covers multiple integration paths. Jumping straight into code without confirming which path the user wants wastes effort and generates dead code that has to be deleted.
**Fix:** BEFORE writing any code, confirm the architecture. Ask or use `clarify` with these options:
1. **Same-machine Python** → subprocess only (no server, no HTTP)
2. **Network server** → FastAPI HTTP bridge (multi-client access)
3. **On-device Android** → Termux + RUN_COMMAND Intent (NO Python — pure Kotlin IPC)
4. **Event-driven** → Webhooks or cron
Only scaffold files for the chosen path. If the user mentions "Android" + "Termux", that's path 3 — no Python, no FastAPI, no systemd.

### Pitfall: File upload PermissionError
**Symptom:** `POST /files/in` returns 500 with `PermissionError: [Errno 13]` if upload dir doesn't exist or isn't writable.
**Fix:** Use `_ensure_dir()` helper that catches `PermissionError` and returns HTTP 500 with a clear message instead of a raw traceback.

### Pitfall: `hermes proxy` used instead of `hermes chat -q`
**Symptom:** External app gets raw model responses with no skill loading, no tool execution, no agent loop.
**Fix:** Use `hermes chat -q -z` for any call that needs the full agent experience. `hermes proxy` is only for raw model access (like pointing Codex CLI at it).

### Pitfall: Skills not persisting across session resume
**Symptom:** Skill loaded in turn 1 doesn't auto-load in turn 2 after `--resume`.
**Fix:** Skills re-match each turn based on prompt content. Force-load critical skills with `-s skillname` on every call.

### Pitfall: Context length not configurable via API
**Symptom:** Ollama model has tiny context (2K-4K), Hermes loses tool schemas.
**Fix:** Set context length server-side (Ollama Modelfile or `OLLAMA_CONTEXT_LENGTH` env var), not through the OpenAI-compatible API.

### Pitfall: Timeout on complex agent tasks
**Symptom:** Subprocess call times out during multi-step skill execution.
**Fix:** Set generous timeouts (300-600s). For slow local models, set `HERMES_API_TIMEOUT=1800` in `.env`.

## Architecture Decision: Which Integration Path?

| Need | Use |
|---|---|
| Call Hermes from Python (same machine) | `subprocess.run(["hermes", "chat", "-q", "-z", ...])` |
| Call Hermes from any client over network | FastAPI HTTP bridge (see `templates/`) |
| Call Hermes from Android (on-device) | Termux + RUN_COMMAND Intent (see `references/android-termux.md`) |
| Use Hermes as MCP tool | `hermes mcp serve` |
| Trigger Hermes from external events | Webhook subscriptions (`hermes webhook subscribe`) |
| Schedule recurring Hermes tasks | Cron jobs (`hermes cron create`) |

## References

- `references/local-llm-setup.md` — Ollama/llama.cpp integration, model sizing, benchmarks
- `references/android-termux.md` — On-device Hermes via Termux + Intent IPC (no server)

## Templates

- `templates/` — Complete FastAPI bridge project (main.py, routes, hermes_bridge.py, config, systemd, Dockerfile, Makefile)
- `templates/hermes_client.py` — Python client library for the HTTP bridge
- `templates/test_api.py` — Self-contained 14-test verification suite
- `templates/hermes_bridge.sh` — Shell wrapper for Android/Termux that outputs JSON (session_id + response) for Kotlin parsing

### Pitfall: Hermes venv PYTHONPATH leak when running API bridge tests
**Symptom:** `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'` when running tests with system `python3` or even inside a project venv.
**Cause:** Hermes terminal exports its Python 3.11 PYTHONPATH globally. This leaks into project venvs, causing system `python3` (which may be 3.9) to try loading Hermes's 3.11 C-extension wheels — which crash.
**Fix (3 steps, verified working):**
1. Create a project-local venv: `/usr/bin/python3 -m venv --clear .venv`
2. Bootstrap pip in isolation: `env -i HOME="$HOME" .venv/bin/python3 -m ensurepip --upgrade`
3. Install deps with PYTHONPATH cleared: `PYTHONPATH="" .venv/bin/pip3 install fastapi httpx pydantic pyyaml python-multipart aiofiles uvicorn`
4. Run tests with: `PYTHONPATH="" .venv/bin/python3 tests/test_api.py`
5. In the Makefile, hardcode: `test: PYTHONPATH="" .venv/bin/python3 tests/test_api.py`
**Why `env -i` alone fails:** Stripping the entire environment can cause pip itself to hang during network operations. Clearing just `PYTHONPATH` while preserving `HOME` and `PATH` is the sweet spot.

### Pitfall: `terminal` tool falsely rejects `pip install` as a server process
**Symptom:** `pip install` in foreground mode rejected with: "This foreground command appears to start a long-lived server/watch process."
**Cause:** The terminal tool's heuristic misidentifies pip as a long-running process.
**Fix:** Use `background=true` with `notify_on_complete=true`, then `process(action='wait')` to collect the result. Or use `execute_code` with `hermes_tools.terminal()` which doesn't have this heuristic.

## Related Skills

- `hermes-agent` — Core Hermes configuration, CLI reference, provider setup
- `web-service-launch` — Launching web services on specific ports

## HTTP-Server Deep Dives (absorbed from hermes-api-bridge)

Three reference files from the former `hermes-api-bridge` skill cover the network-server path in depth:
- `references/http-fastapi-server.md` — full FastAPI app, routes, subprocess bridge, auth
- `references/http-deployment.md` — systemd service, Docker Compose, Nginx TLS, install scripts
- `references/http-client-patterns.md` — Python client library, ChainLit integration, Android Kotlin client, curl examples

## Overlap Note

This skill is the single umbrella for all Hermes integration paths. The former `hermes-api-bridge` (devops) covered only the HTTP server subset and has been merged into this skill (its reference files live here under `http-*.md`).
