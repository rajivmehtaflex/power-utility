# Pyodide Worker Architecture — Code Patterns

This reference uses a Promise resolver map for cross-thread LLM responses. Do not re-enter Pyodide for `LLM_RESPONSE` while a `runPythonAsync` ReAct task is awaiting.

## Main thread: host_bridge.js

```javascript
export const MessageType = {
    LLM_REQUEST: "LLM_REQUEST",
    LLM_RESPONSE: "LLM_RESPONSE",
    LLM_ERROR: "LLM_ERROR",
    AGENT_LOG: "AGENT_LOG",
    AGENT_COMPLETE: "AGENT_COMPLETE",
    AGENT_ERROR: "AGENT_ERROR",
    START_LOOP: "START_LOOP"
};

export class PromptChainHost {
    constructor(workerScriptUrl) {
        this.worker = new Worker(workerScriptUrl, { type: "classic" });
        this.session = null;
        this.pendingRequests = new Map();
        this.messageIdSeq = 0;
        this.worker.onmessage = this.handleWorkerMessage.bind(this);
        this.worker.onerror = (event) => {
            this.rejectPending(new Error(event.message || "Worker error"));
        };
    }

    async init(systemPrompt) {
        if (typeof window.LanguageModel === "undefined") {
            throw new Error("LanguageModel not supported.");
        }
        // Invoke create before any await; call init from a user click/tap when
        // availability is downloadable/downloading.
        this.session = await window.LanguageModel.create({
            systemPrompt,
            outputLanguage: "en"
        });
    }

    async handleWorkerMessage(event) {
        const { id, type, payload } = event.data;
        if (type === MessageType.LLM_REQUEST) {
            try {
                if (!this.session) throw new Error("LLM Session not initialized.");
                const response = await this.session.prompt(payload.prompt, {
                    responseConstraint: payload.schema
                });
                this.worker.postMessage({
                    id,
                    type: MessageType.LLM_RESPONSE,
                    payload: typeof response === "string"
                        ? response
                        : JSON.stringify(response)
                });
            } catch (error) {
                this.worker.postMessage({
                    id,
                    type: MessageType.LLM_ERROR,
                    payload: `LLM bridge error: ${error.message || error}`
                });
            }
            return;
        }
        if (type === MessageType.AGENT_COMPLETE) {
            const pending = this.pendingRequests.get(id);
            if (pending) {
                pending.resolve(payload);
                this.pendingRequests.delete(id);
            }
            return;
        }
        if (type === MessageType.AGENT_ERROR) {
            this.rejectPending(new Error(payload), id);
        }
    }
}
```

## Worker: worker_proxy.js

```javascript
const pendingLlmRequests = new Map();
let nextRequestId = 1;
let activeTaskId = 0;

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

function postAgentMessage(jsonText) {
    self.postMessage(JSON.parse(jsonText));
}

self.onmessage = async ({ data }) => {
    if (data.type === "LLM_RESPONSE" || data.type === "LLM_ERROR") {
        const pending = pendingLlmRequests.get(data.id);
        if (!pending) return;
        pendingLlmRequests.delete(data.id);
        data.type === "LLM_RESPONSE"
            ? pending.resolve(data.payload)
            : pending.reject(new Error(data.payload));
        return; // Never run Pyodide from this branch.
    }

    if (data.type !== "START_LOOP") return;
    activeTaskId = data.id;
    const pyodide = await agentReady;
    pyodide.globals.set("_task_id", data.id);
    pyodide.globals.set("_user_prompt", data.payload);
    await pyodide.runPythonAsync(
        "await agent_core.dispatch_start(_task_id, _user_prompt)"
    );
};

async function initAgent(pyodide) {
    const [agentResp, toolsResp] = await Promise.all([
        fetch("/python/agent_core.py"),
        fetch("/python/tools.py")
    ]);
    pyodide.FS.writeFile("agent_core.py", await agentResp.text());
    pyodide.FS.writeFile("tools.py", await toolsResp.text());
    pyodide.globals.set("worker_request_llm", requestLlm);
    pyodide.globals.set("worker_post_message", postAgentMessage);
    await pyodide.runPythonAsync("import agent_core");
    await pyodide.runPythonAsync(
        "agent_core.setup_bridges(worker_request_llm, worker_post_message)"
    );
    await pyodide.runPythonAsync("agent_core.init_agent()");
}
```

## Python: agent_core.py

```python
import json

_request_llm = None
_post_to_js = None


def setup_bridges(request_llm, post_message):
    global _request_llm, _post_to_js
    _request_llm = request_llm
    _post_to_js = post_message


async def ask_llm(prompt):
    return await _request_llm(prompt, json.dumps(AGENT_JSON_SCHEMA))


def post_to_host(msg_id, msg_type, payload):
    _post_to_js(json.dumps({
        "id": msg_id,
        "type": msg_type,
        "payload": payload,
    }))
```

## Static server

Serve Worker assets with absolute paths and COOP/COEP headers:

```python
self.send_header("Cross-Origin-Opener-Policy", "same-origin")
self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
```

Use `fetch("/python/agent_core.py")`, not `fetch("./python/agent_core.py")` from `/js/worker_proxy.js`.
