# Chrome Prompt API + Pyodide Worker Debugging Reference

Session-derived reference for browser-native LLM sessions hosted on the main thread while a Python ReAct loop runs in a Pyodide Web Worker.

## Failure signatures and root causes

### 1. Button stays disabled at `Running agent...`

Likely causes:

- `LanguageModel.create()` was called during `DOMContentLoaded` while availability was `downloadable` or `downloading`.
- The Worker re-entered Pyodide with `runPython()` for an LLM response while `runPythonAsync()` was already awaiting that response.
- A Python dict/PyProxy was passed to `postMessage()` and the Worker failed before emitting a visible error.

Observed Chrome error for the first cause:

```text
Requires a user gesture when availability is "downloading" or "downloadable".
```

### 2. UI shows repeated LLM failures

If the Python loop logs repeated errors such as:

```text
LLM request or response parsing failed: Error: LLM Session not initialized.
```

The Run button was allowed before main-thread model initialization finished. Gate the run path or initialize the session directly inside the user click handler.

### 3. No Python asset requests

If `/python/agent_core.py` and `/python/tools.py` are absent from server logs, the main-thread model session has not reached the Worker start path. Inspect model availability/session initialization before debugging Pyodide.

## Reliable architecture

```text
user click
  └─ LanguageModel.create(...) called synchronously before first await
       └─ main-thread host owns session.prompt(...)
            ↕ postMessage
       Worker owns JS Promise resolver map
            └─ Python awaits injected JS request function
                 └─ pyodide.runPythonAsync("await dispatch_start(...)")
```

The `LLM_RESPONSE` handler only resolves a JavaScript Promise. It must never invoke `pyodide.runPython()` while the ReAct task is awaiting.

### Worker-side Promise bridge

```javascript
const pendingLlmRequests = new Map();
let nextRequestId = 1;

function requestLlm(prompt, schemaJson) {
    const id = nextRequestId++;
    return new Promise((resolve, reject) => {
        pendingLlmRequests.set(id, { resolve, reject });
        self.postMessage({
            id,
            type: "LLM_REQUEST",
            payload: { prompt, schema: JSON.parse(schemaJson) }
        });
    });
}

self.onmessage = async ({ data }) => {
    if (data.type === "LLM_RESPONSE" || data.type === "LLM_ERROR") {
        const pending = pendingLlmRequests.get(data.id);
        if (!pending) return;
        pendingLlmRequests.delete(data.id);
        if (data.type === "LLM_RESPONSE") {
            pending.resolve(data.payload);
        } else {
            pending.reject(new Error(data.payload));
        }
        return;
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

### Python bridge

```python
async def ask_llm(prompt):
    # _request_llm is a JS function returning a JS Promise.
    return await _request_llm(prompt, json.dumps(AGENT_JSON_SCHEMA))

def _post_to_host(msg_id, msg_type, payload):
    # JSON text avoids passing a PyProxy through structured clone.
    _post_to_js(json.dumps({
        "id": msg_id,
        "type": msg_type,
        "payload": payload,
    }))
```

### Main-thread session initialization

```javascript
async init(systemPrompt) {
    // No availability() await before create(). The call must occur in the
    // click/tap activation path when the model is downloadable/downloading.
    this.session = await window.LanguageModel.create({
        systemPrompt,
        outputLanguage: "en"
    });
}
```

Initialize the Worker during page load if desired, but call `host.init()` from the Run button’s event handler. Display `LanguageModel.availability()` separately as status (`available`, `downloadable`, `downloading`, `unavailable`).

## Tool-input validation in ReAct loops

A valid JSON response can still select a tool with an empty `toolInput`. Do not pass that value directly to the tool. For a calculator, an empty string reaches `ast.parse(..., mode="eval")` and produces `Math Evaluation Error: invalid syntax`.

Use three layers of protection:

1. Describe the tool contract explicitly: calculator input must be a non-empty raw expression such as `2 * 2`, not a natural-language question.
2. Validate `toolInput` before execution. If it is empty, recover only deterministic, simple arithmetic forms from the original user prompt (for example, `2 multiplied by 2` → `2 * 2`). If recovery is not safe, append an observation asking the model for a non-empty input and continue the loop.
3. Add a regression test where the first model response selects `calculator` with an empty input. Assert the tool observes `4` (or the expected result) and never emits an invalid-syntax observation.

The recovery is a guardrail, not a replacement for a clear model prompt/schema. Keep the raw recovered expression visible in the observability log so debugging can distinguish model output from deterministic repair.

## Verification recipe

Run from the repository root:

```bash
node --check static/js/host_bridge.js
node --check static/js/worker_proxy.js
uv run pytest tests/ -q
```

Then verify in the browser:

1. Refresh with cache busting.
2. Confirm the Run button is enabled before model initialization.
3. Confirm the status distinguishes model download from app failure.
4. Click Run Agent once; model creation must start from that gesture.
5. Server logs should show `/python/agent_core.py` and `/python/tools.py` with HTTP 200.
6. The log should show `--- Iteration 1 ---` and then either an `AGENT_COMPLETE` result or a visible `AGENT_ERROR`.
7. A Worker error must settle the pending task; the UI must not remain disabled indefinitely.

A focused ad-hoc verification script should also assert that the served HTML/JS contains the user-gesture initialization and Promise bridge markers, then run the project’s canonical tests. Remove the temporary script afterward.
