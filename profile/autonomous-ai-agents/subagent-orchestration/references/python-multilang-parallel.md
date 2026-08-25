# Python + JS/Browser Parallel Execution Patterns

Worked patterns from orchestrating a multi-language project (Python tools + JS bridge + HTML UI + PyScript WASM) through parallel subagent waves.

## Project Shape: Multi-Language Browser App

Unlike a pure JS project, browser apps with a Python backend (PyScript/Pyodide) have code spread across multiple languages and directories:

```
project/
├── pyproject.toml          ← Wave 0: uv project config
├── static/
│   ├── index.html          ← Wave 1: frontend UI
│   ├── pyscript.toml       ← Wave 1: PyScript config
│   ├── js/
│   │   ├── host_bridge.js  ← Wave 1: main-thread bridge
│   │   └── worker_proxy.js ← Wave 1: worker bootstrap
│   └── python/
│       ├── tools.py        ← Wave 1: Python tools
│       └── agent_core.py   ← Wave 1: ReAct engine
├── scripts/
│   └── dev_server.py       ← Wave 1: COOP/COEP server
└── tests/
    ├── test_calculator.py  ← Wave 1: unit tests
    └── test_summarizer.py  ← Wave 1: unit tests
```

## Lane Decomposition for 5 Parallel Subagents

Each subagent owns a **different directory or file** — zero conflict risk:

| Lane | Files Owned | Language |
|------|-------------|----------|
| 1 | `static/python/tools.py` + `tests/test_*.py` | Python |
| 2 | `static/python/agent_core.py` | Python |
| 3 | `static/js/host_bridge.js` + `worker_proxy.js` | JavaScript |
| 4 | `static/pyscript.toml` + `static/index.html` | TOML + HTML |
| 5 | `scripts/dev_server.py` | Python |

## Verification by Language (Orchestrator Direct)

After all Wave 1 subagents complete, run **language-specific syntax checks** on each file:

```bash
# Python — ast.parse is lightweight and doesn't execute imports
uv run python -c "import ast; ast.parse(open('file.py').read()); print('OK')"

# JavaScript — node --check validates syntax without executing
node --check file.js

# TOML — use tomllib for structural validation
uv run python -c "import tomllib; tomllib.load(open('file.toml','rb'))"
```

**Pitfall:** Python files with Pyodide/PyScript imports (`from js import self`, `from pyodide.ffi import create_proxy`) will fail at import time in standard Python. Use `ast.parse` (syntax-only) for verification — never `import` them.

## Dev Server Smoke Test Pattern (Web Apps)

```
# Step 1: Start server in background
terminal(background=true, command="uv run python scripts/dev_server.py")

# Step 2: Wait briefly, then verify headers and content
terminal("curl -sI http://localhost:8123 | head -10")  # COOP/COEP headers
terminal("curl -s http://localhost:8123 | head -5")     # HTML served

# Step 3: Kill server
process(action=kill, session_id=...)
```

## Subagent Context Pattern: Embed Complete File Contents

When the plan already specifies exact code (from a playbook or spec), embed it **verbatim** in the subagent's `context` field. The subagent writes the file, not designs it. This is critical for:

1. **Specs with exact code** — playbook/spec documents that provide ready-to-use implementations
2. **Generated code** — code already produced by a planning step that just needs to land on disk
3. **Consistency requirements** — when multiple files must match exact export/import names

**When NOT to embed:** Let the subagent design code when the plan describes *behavior* but not *implementation* (e.g., "create a tool that safely evaluates arithmetic expressions" without providing the AST evaluator code).

## Pyodide-in-Worker Runtime Pitfalls

After Wave 1 files are written and syntax-verified, browser runtime testing surfaces bugs that static checks cannot catch. These three bugs all produce **silent failure** — no console errors, no logs, just a stuck "Running agent..." state.

### Bug 1: Worker Type Mismatch (silent crash)

**Symptom:** Worker never loads; no requests for `worker_proxy.js` in server logs; `GET /undefined` 404 instead.

**Cause:** `new Worker(url, { type: 'module' })` creates a module worker, but `importScripts()` (used inside `worker_proxy.js` to load Pyodide from CDN) is **only available in classic workers**. The worker silently fails to initialize.

**Fix:** Use `{ type: 'classic' }` when the worker uses `importScripts()`:
```javascript
// host_bridge.js
this.worker = new Worker(workerScriptUrl, { type: 'classic' });
```

**Note:** `host_bridge.js` can still use ES module `export` syntax — it's loaded by the main thread's `<script type="module">`, not by the worker. Only the worker file itself must be classic.

### Bug 2: Missing Constructor Argument (undefined Worker URL)

**Symptom:** Server log shows `GET /undefined HTTP/1.1" 404`.

**Cause:** The `PromptChainHost` constructor expects a `workerScriptUrl` argument, but `index.html` calls `new PromptChainHost()` with no argument. The Worker receives `undefined` as its URL.

**Fix:** Always pass the worker path explicitly:
```javascript
const host = new PromptChainHost('./js/worker_proxy.js');
```

### Bug 3: PostMessage Payload Structure Mismatch

**Symptom:** Agent logs appear blank or `[undefined]` in the UI, even though the ReAct loop is executing.

**Cause:** Python sends `payload` as a plain string (`"--- Iteration 1 ---"`), but the HTML's event listener expects an object (`{ message: "...", type: "Thought" }`). The `host_bridge.js` dispatcher passes the raw string through to `CustomEvent`, and the HTML reads `e.detail.message` → `undefined`.

**Fix:** Normalize payloads in `host_bridge.js`:
```javascript
case MessageType.AGENT_LOG:
    window.dispatchEvent(new CustomEvent('agent-log', {
        detail: typeof payload === 'string'
            ? { message: payload, type: 'info' }
            : payload
    }));
    break;
```

And have Python send structured payloads:
```python
def log(self, message, log_type="info"):
    self._post_to_host(0, "AGENT_LOG", {"message": message, "type": log_type})
```

### Bug 4: Pyodide postMessage Bridge Gap

**Symptom:** Python `js.postMessage()` doesn't reach the main thread; agent runs but nothing appears in UI.

**Cause:** Pyodide's `import js` inside a Worker maps `js` to the `WorkerGlobalScope`, which does have `postMessage`. However, the mapping isn't always reliable across Pyodide versions. Messages may silently vanish.

**Fix:** Explicitly expose a bridge function from JS to Python:
```javascript
// worker_proxy.js — after Pyodide loads
pyodide.globals.set("worker_post_message", (msg) => {
    self.postMessage(msg);
});
```

```python
# agent_core.py — _post_to_host
try:
    js._worker_post(msg)
except Exception:
    js.postMessage(msg)  # fallback
```

### Diagnostic Checklist for Silent Worker Failures

When the agent UI is stuck and no errors appear:

1. **Check server logs** — look for `GET /undefined` (missing worker URL), missing `GET /js/worker_proxy.js` (worker never spawned), or `GET /python/*.py` 404s (Pyodide can't fetch Python files).
2. **Open DevTools Console** — module/classic worker type mismatch shows as a silent failure, not an error.
3. **Open DevTools → Network tab** — verify `worker_proxy.js` loads with 200, and Pyodide CDN requests succeed.
4. **Check DevTools → Application → Workers** — if no worker appears, the Worker constructor failed.

## uv-Specific Notes

- `uv sync` alone does NOT install `[project.optional-dependencies]` groups — use `uv sync --extra dev`
- `uv init` creates a `src/` layout by default; for browser apps, `src/` is just a build-system placeholder
- `uv run pytest tests/ -v` works from project root without activating venv
- `uv run python scripts/dev_server.py` runs server scripts with the project venv
