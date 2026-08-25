---
name: pyscript-pyodide-worker
description: Pyodide WASM apps in Web Workers. Use for Python-in-browser.
metadata:
  hermes_tags: pyscript, pyodide, wasm, web-worker, browser
---

# PyScript / Pyodide Web Worker Applications

Build Python-in-the-browser apps where Pyodide runs inside a Web Worker, with async loops (ReAct agents, streaming inference) and main-thread bridges to browser APIs (Chrome Prompt API, DOM).

## Architecture pattern

```
index.html (main thread)
  └─ host_bridge.js (main thread)
       ├─ Holds browser API sessions (LanguageModel, etc.)
       ├─ Creates Worker('worker_proxy.js', { type: 'classic' })
       └─ RPC via postMessage <-> Worker
            └─ worker_proxy.js (Worker)
                 ├─ importScripts(pyodide.js)
                 ├─ Fetches .py files, writes to pyodide.FS
                 ├─ Sets up JS<->Python bridge via globals.set()
                 └─ pyodide.runPythonAsync() for async ops
                      └─ agent_core.py (Pyodide)
                           ├─ asyncio coroutines
                           └─ Calls bridge to postMessage back to main thread
```

## Worker type constraint — the #1 gotcha

**`importScripts()` only works in classic workers. ES module workers (`type: 'module'`) do NOT support `importScripts`.**

```javascript
// CORRECT — classic worker, importScripts works
this.worker = new Worker(url, { type: 'classic' });

// WRONG — module worker, importScripts throws
this.worker = new Worker(url, { type: 'module' });
```

BUT: the main-thread file that `import`s classes referencing the worker (like `host_bridge.js` using `export class`) must still be loaded via `<script type="module">` in HTML. The Worker type only affects the worker script itself, not files that create the worker.

## Relative path resolution in Workers

`fetch("./file.py")` inside a Worker resolves relative to the **Worker script's URL**, not the page URL. If the worker is at `/js/worker_proxy.js`, then `fetch("./python/agent_core.py")` becomes `/js/python/agent_core.py` (404).

**Fix: use absolute paths from server root:**
```javascript
fetch("/python/agent_core.py")  // always resolves correctly
fetch("/python/tools.py")
```

## Pyodide async event loop in Workers

Pyodide integrates `asyncio` with JS Promises automatically **when called via `runPythonAsync`**. A Python `await` on a JS Promise will pump the event loop naturally.

### Do not re-enter Pyodide for awaited responses

A common deadlock is:

1. `START_LOOP` calls `runPythonAsync("await ...")`.
2. Python awaits an LLM response.
3. The Worker receives `LLM_RESPONSE` and calls `pyodide.runPython(...)` again.
4. The second Python invocation cannot safely re-enter the still-running async invocation, so the response future is never resolved.

Use a **JavaScript Promise resolver map** instead. Python awaits a JS function that returns a Promise; the Worker resolves/rejects that Promise directly when the response arrives. The response handler must not call Pyodide.

```javascript
const pendingLlmRequests = new Map();

function requestLlm(prompt, schemaJson) {
    const id = nextRequestId++;
    return new Promise((resolve, reject) => {
        pendingLlmRequests.set(id, { resolve, reject });
        self.postMessage({ id, type: "LLM_REQUEST", payload: {
            prompt, schema: JSON.parse(schemaJson)
        }});
    });
}

self.onmessage = async ({ data }) => {
    if (data.type === "LLM_RESPONSE" || data.type === "LLM_ERROR") {
        const pending = pendingLlmRequests.get(data.id);
        if (pending) {
            pendingLlmRequests.delete(data.id);
            data.type === "LLM_RESPONSE"
                ? pending.resolve(data.payload)
                : pending.reject(new Error(data.payload));
        }
        return; // Never call pyodide.runPython here.
    }

    if (data.type === "START_LOOP") {
        const pyodide = await agentReady;
        pyodide.globals.set("_task_id", data.id);
        pyodide.globals.set("_user_prompt", data.payload);
        await pyodide.runPythonAsync(
            "await agent_core.dispatch_start(_task_id, _user_prompt)"
        );
    }
};
```

Python receives the JS Promise bridge and awaits it directly:

```python
_request_llm = None

def setup_bridges(request_llm, post_message):
    global _request_llm, _post_to_js
    _request_llm = request_llm
    _post_to_js = post_message

async def ask_llm(prompt):
    return await _request_llm(prompt, json.dumps(AGENT_JSON_SCHEMA))
```

Avoid `asyncio.create_task()` alone in Pyodide—the task may be scheduled without the event loop being pumped. Keep one top-level `runPythonAsync` invocation for the task and let JS Promises suspend/resume it.

### Safe Pyodide-to-JS payloads

A Python `dict` crossing a `JsProxy` callback may arrive as a `PyProxy`, which `postMessage()` cannot structured-clone. Serialize before invoking the bridge and parse in JavaScript:

```python
_post_to_js(json.dumps({"id": msg_id, "type": msg_type, "payload": payload}))
```

```javascript
function postAgentMessage(jsonText) {
    self.postMessage(JSON.parse(jsonText));
}
```

## JS-to-Python bridge setup

Python can't directly call `self.postMessage()` in a Worker. Inject two explicit bridges during Pyodide initialization: one JS function that returns an LLM Promise, and one JSON-text message emitter.

```javascript
function postAgentMessage(jsonText) {
    self.postMessage(JSON.parse(jsonText));
}

pyodide.globals.set("worker_request_llm", requestLlm);
pyodide.globals.set("worker_post_message", postAgentMessage);
await pyodide.runPythonAsync(
    "agent_core.setup_bridges(worker_request_llm, worker_post_message)"
);
```

```python
_request_llm = None
_post_to_js = None

def setup_bridges(request_llm, post_message):
    global _request_llm, _post_to_js
    _request_llm = request_llm
    _post_to_js = post_message

def _post_to_host(msg_id, msg_type, payload):
    if _post_to_js:
        _post_to_js(json.dumps({
            "id": msg_id, "type": msg_type, "payload": payload
        }))
```

Do not pass Python dictionaries directly to a JS callback that calls `postMessage`; PyProxy objects are not reliably structured-cloneable.

## Pyodide-specific Python gotchas

### `from js import self` breaks standard Python
The `js` module only exists inside Pyodide. Moving `from js import self` / `from pyodide.ffi import create_proxy` inside `__init__` or method bodies allows the file to pass `ast.parse` and be syntax-checked outside WASM.

### `ast.Num` removed in Python 3.12+
Use `ast.Constant` for literal evaluation. `ast.Num` is deprecated since 3.8 and removed in 3.14.

### Single message dispatch
Don't register `self.addEventListener("message", ...)` in Python AND `self.onmessage` in JS — this double-dispatches every message. Handle all dispatch in JS and call Python explicitly.

## COOP/COEP headers for WASM

Web Workers with WASM (especially with SharedArrayBuffer) require cross-origin isolation headers. The dev server must send:

```python
self.send_header("Cross-Origin-Opener-Policy", "same-origin")
self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
```

Verify with: `curl -sI http://localhost:PORT | grep -i cross-origin`

### COEP blocks cross-origin CDN scripts

`Cross-Origin-Embedder-Policy: require-corp` blocks **any** cross-origin resource that doesn't send a `Cross-Origin-Resource-Policy` header — including popular CDN scripts like `cdn.tailwindcss.com`. The browser console shows:

```text
net::ERR_BLOCKED_BY_RESPONSE.NotSameOriginAfterDefaultedToSameOriginByCoep
```

Adding `crossorigin="anonymous"` to the `<script>` tag does **not** fix this — the CDN must itself set CORP headers, which most don't. Solutions:

1. **Remove the CDN dependency** — inline local CSS or bundle the library. This is the reliable fix.
2. **Switch to `credentialless`** COEP (`Cross-Origin-Embedder-Policy: credentialless`) — Chrome-only, allows loading cross-origin resources without CORP, but not universally supported.
3. **Self-host the CDN asset** — download and serve from your own static directory.

Never leave a broken CDN `<script>` tag in place under `require-corp` COEP; it fails silently and the page renders unstyled.

## Browser API user-gesture constraints

Browser-local model APIs may reject or indefinitely delay initialization when invoked during page load. Chrome Prompt API is especially important: `LanguageModel.create()` requires a user gesture when availability is `downloadable` or `downloading`.

- Do not call `LanguageModel.create()` from `DOMContentLoaded`.
- Instantiate the Worker during page load if desired, but call `create()` directly inside the click/tap handler.
- Call `create()` before the first `await` in that handler path; an earlier awaited availability check may consume the transient activation.
- Surface `LanguageModel.availability()` in the UI (`available`, `downloadable`, `downloading`, `unavailable`) so a model download is distinguishable from a frozen Worker.
- Add a timeout and visible failure path around model initialization.

## Error propagation and completion

Every request must have a completion/error route:

- `LLM_REQUEST` → main thread calls the browser model.
- `LLM_RESPONSE`/`LLM_ERROR` → Worker resolves/rejects the JS Promise map without entering Pyodide.
- `AGENT_COMPLETE`/`AGENT_ERROR` → main thread settles the request Promise.
- Worker `onerror` and `onmessageerror` should reject pending requests.
- Use request IDs for task completion, but treat an unscoped Worker error (`id: 0`) as fatal for all pending tasks.
- Add a finite timeout so the UI cannot remain disabled forever.

## Debugging checklist

When the Worker loads but nothing happens:
1. **Check server logs** for 404s on `.py` files — path resolution bug
2. **Check Worker type** matches `importScripts` vs `import` usage
3. **Check if `runPythonAsync` is used** for async Python (not `runPython`)
4. **Check for concurrent Pyodide re-entry** — LLM responses must resolve JS Promises, not call `runPython` while `runPythonAsync` is awaiting
5. **Check bridge setup** — both `_request_llm` and `_post_to_js` must be set before agent init
6. **Check payload conversion** — JSON-serialize Python dictionaries before passing them to `postMessage`
7. **Check user activation** — `LanguageModel.create()` must be in a click/tap path when model availability is `downloadable`/`downloading`
8. **Check availability status** — distinguish model downloading from a Worker failure
9. **Check for double-dispatch** — only one `onmessage` handler should exist
10. **DevTools** — Worker errors only show in the Worker's console scope (chrome://inspect, Workers tab)

See `references/pyodide-worker-architecture.md` for the full Promise-bridge pattern, safe JSON payloads, and a compact host/Worker/Python skeleton.

## See also

- `references/pyodide-worker-architecture.md` — compact host/Worker/Python Promise-bridge skeleton.
- `references/chrome-prompt-api-session-debugging.md` — project-specific debugging patterns, AGENTS.md workflow, calculator input recovery, and end-to-end verification checklist for Chrome Prompt API implementations.
