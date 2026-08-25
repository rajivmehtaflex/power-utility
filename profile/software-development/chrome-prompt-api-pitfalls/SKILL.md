---
name: chrome-prompt-api-pitfalls
description: Use for Chrome Prompt API, Pyodide WASM, or COEP apps.
---

# Chrome Prompt API + Pyodide WASM Agent Pitfalls

Learned from a debugging session where silent failures hung the agent indefinitely. Each pitfall below produces **no console error** — the app just stops responding.

## Pitfall 1: LanguageModel.create() must be inside a user gesture

**Symptom:** "Running agent..." hangs forever. No error in console.

**Root cause:** Chrome's Prompt API requires `window.LanguageModel.create()` to fire **synchronously within a user gesture** (click handler). If called from `DOMContentLoaded`, after an `await`, or in a `.then()` chain, Chrome silently refuses or throws a swallowed `NotAllowedError`.

**Fix — call create() directly in the click handler before any await:**
```javascript
runBtn.addEventListener('click', async () => {
  if (!hostReady) {
    // LanguageModel.create() runs BEFORE any await — stays in gesture context
    await host.init(SYSTEM_PROMPT);
    hostReady = true;
  }
  // ...now safe to await other things
});
```

## Pitfall 2: COEP `require-corp` blocks all cross-origin CDNs

**Symptom:** `net::ERR_BLOCKED_BY_RESPONSE.NotSameOriginAfterDefaultedToSameOriginByCoep` in console. Page renders unstyled or missing scripts.

**Root cause:** `Cross-Origin-Embedder-Policy: require-corp` (needed for WASM/SharedArrayBuffer) blocks ANY cross-origin resource that doesn't send `Cross-Origin-Resource-Policy` headers. Adding `crossorigin="anonymous"` to the `<script>` tag does **not** fix this — the CDN origin must itself send CORP headers, which most don't.

**Fix — remove the CDN entirely, use inline CSS or locally-bundled assets:**
```html
<!-- BAD: blocked by COEP regardless of crossorigin -->
<script src="https://cdn.tailwindcss.com" crossorigin="anonymous"></script>

<!-- GOOD: hand-write CSS or bundle Tailwind locally -->
<style>
  :root { color-scheme: dark; font-family: system-ui, sans-serif; }
  /* ... minimal CSS ... */
</style>
```

## Pitfall 3: No timeout = silent hang forever

**Symptom:** Agent never completes, no error, button stays disabled.

**Root cause:** If the LLM session fails silently (e.g., Pitfall 1), the `runAgent()` Promise never resolves or rejects. With no timeout, the UI hangs indefinitely.

**Fix — always add a timeout + worker.onerror handler:**
```javascript
runAgent(userPrompt) {
  return new Promise((resolve, reject) => {
    const id = ++this.messageIdSeq;
    const timeout = setTimeout(() => {
      if (this.pendingRequests.has(id)) {
        this.pendingRequests.delete(id);
        reject(new Error('Agent timed out after 90 seconds.'));
      }
    }, 90000);
    this.pendingRequests.set(id, {
      resolve: (v) => { clearTimeout(timeout); resolve(v); },
      reject: (e) => { clearTimeout(timeout); reject(e); }
    });
    this.worker.postMessage({ id, type: 'START_LOOP', payload: userPrompt });
  });
}

// In constructor:
this.worker.onerror = (event) => {
  this.rejectPending(new Error(event.message || 'Unknown worker error.'));
};
```

## Pitfall 4: Small models (Gemini Nano) frequently omit toolInput

**Symptom:** Agent loops to max iterations and returns "Execution halted." even when it correctly selected the right tool.

**Root cause:** Gemini Nano is a ~2B parameter model. It often returns the correct `toolName` (e.g., `"calculator"`) but leaves `toolInput` empty (`""`), causing the tool to fail on empty input.

**Fix — recover tool input from the user prompt via regex fallback:**
```python
import re

_NUMBER = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
_CALCULATOR_PATTERNS = (
    (rf"({_NUMBER})\s*(?:multiplied\s+by|times|x|\*)\s*({_NUMBER})", "*"),
    (rf"({_NUMBER})\s*(?:divided\s+by|over|/)\s*({_NUMBER})", "/"),
    (rf"({_NUMBER})\s*(?:plus|\+)\s*({_NUMBER})", "+"),
    (rf"({_NUMBER})\s*(?:minus|-)\s*({_NUMBER})", "-"),
)

def recover_tool_input(tool_name, user_prompt):
    if tool_name != "calculator":
        return ""
    for pattern, operator_symbol in _CALCULATOR_PATTERNS:
        match = re.search(pattern, user_prompt, flags=re.IGNORECASE)
        if match:
            return f"{match.group(1)} {operator_symbol} {match.group(2)}"
    return ""
```

## Architecture pattern that works

The Pyodide Worker + JS Promise bridge pattern is sound:

```
Host (main thread)          Worker (worker_proxy.js)       Pyodide (WASM Python)
───────────────────         ──────────────────────         ─────────────────────
click → runAgent()          onmessage(START_LOOP)          dispatch_start()
  ↕ postMessage             runPythonAsync(await ...)       await ask_llm()
  ↕ postMessage             onmessage(LLM_RESPONSE)         ↕ Promise resolve
session.prompt()            resolveLlmMessage()             ← continues loop
  ↕ postMessage(LLM_RESP)   pendingLlmRequests.get(id)     post AGENT_COMPLETE
```

Key design rules:
- Python `await` on JS Promises is safe — the Pyodide event loop suspends while JS resolves the Promise
- **Never re-enter Pyodide concurrently** — `LLM_RESPONSE` messages only resolve JS Promises, they don't call `runPythonAsync`
- Pass JSON text across the boundary, not dicts/PyProxy objects (structured clone fails)
- Use `pyodide.FS.writeFile()` to load Python modules, then `runPythonAsync("import module")`

## Verification checklist (do ALL before declaring success)

- [ ] `uv run pytest tests/ -v` passes
- [ ] `node --check` passes on all JS files
- [ ] Server responds with COOP/COEP headers
- [ ] **Drove the browser end-to-end** — clicked Run Agent and confirmed a final answer appeared in the UI
- [ ] Console has no red errors after a full run
- [ ] Timeout fires within 90s if something is broken (not silent hang)
