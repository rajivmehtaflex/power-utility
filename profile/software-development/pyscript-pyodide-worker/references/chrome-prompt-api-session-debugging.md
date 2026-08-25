# Chrome Prompt API + Pyodide Worker Session Debugging Patterns

*Session-specific debugging patterns from a Chrome Prompt API + ReAct agent implementation*

## Project AGENTS.md structure

Each Chrome Prompt API project should maintain a project-specific `AGENTS.md` alongside the workspace-level file. Include:

- **Commands section** — exact invocations for `uv sync`, `pytest`, dev server
- **Architecture overview** — e.g., "host bridge → Worker → Pyodide → ReAct loop"
- **Unique constraints** — e.g., "user-gesture init requirement", "no concurrent Pyodide re-entry"
- **Git setup** — e.g., "remote: rajivmehtaflex/Chrome_Prompt_API"
- **Pitfalls and fixes** — all observed and resolved issues

## Dev server workflow

```bash
uv sync --extra dev              # install deps + pytest
uv run pytest tests/ -q          # 12 tests (agent loop, calculator, summarizer)
uv run python scripts/dev_server.py   # COOP/COEP server on :8123
```

Open `http://localhost:8123` in Chrome, wait for "Gemini Nano is ready", click **Run Agent**.

## Calculator tool input recovery pattern

Gemini Nano frequently returns the correct `toolName` but empty `toolInput`. This regression pattern:

- **Pattern**: Model selects `{"toolName": "calculator", "toolInput": ""}`
- **Result**: Calculator tool fails with "invalid syntax" on empty string
- **Fix**: Recover from original user prompt via regex fallback

### Tool description specification

```python
class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Evaluates simple arithmetic expressions. Call ONLY with raw expressions like '2 * 2', never with natural language."
        )
```

### Input recovery implementation

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

### Test for recovery

```python
def test_empty_calculator_input_is_recovered_from_user_prompt():
    recovered = recover_tool_input("calculator", "What is 2 multiplied by 2?")
    assert recovered == "2 * 2"
```

## PyScript WASM Python loading paths

**Critical**: Use absolute paths from server root. Relative paths fail due to Worker URL resolution.

```html
<!-- WRONG: relative from Worker script -->
<script type="text/python" src="./python/agent_core.py"></script>
<!-- Resolves to: /js/python/agent_core.py (404) -->

<!-- CORRECT: absolute from project root -->
<script type="text/python" src="/python/agent_core.py"></script>
<!-- Always resolves correctly -->
```

## Worker message ID tracking

Avoid ID collision between initialization and agent messages:

```javascript
export default class HostBridge {
  constructor() {
    this.messageIdSeq = 0; // separate from Worker's internal IDs
  }
  
  runAgent(userPrompt) {
    return new Promise((resolve, reject) => {
      const id = ++this.messageIdSeq; // unique request ID
      const timeout = setTimeout(() => { /* timeout logic */ }, 90000);
      this.pendingRequests.set(id, { resolve, reject, timeout });
      this.worker.postMessage({ id, type: 'START_LOOP', payload: userPrompt });
    });
  }
}
```

## Host bridge initialization pattern

Ensure `LanguageModel.create()` runs synchronously within user gesture context:

```javascript
runBtn.addEventListener('click', async () => {
  if (!hostReady) {
    // LanguageModel.create() runs BEFORE await — stays in gesture context
    await host.init(SYSTEM_PROMPT);
    hostReady = true;
  }
  // Now safe to await other operations
});
```

## Server cache-busting for live updates

During development, append a cache-busting parameter to force asset refresh:

```html
<script src="/js/host_bridge.js?cachebust=2026-08-04-17-53"></script>
```

## Git workflow for submodules

When committing submodule changes:

1. Commit in submodule directory first:
   ```bash
   cd g-drive-binding && git commit -m "fix: token refresh callback"
   ```

2. Commit parent repository's submodule pointer:
   ```bash
   cd .. && git add g-drive-binding && git commit -m "feat: update submodule to v1.1"
   ```

3. Verify tests before push and validate remote matches account.

## Error propagation chain

Ensure every request has a completion route:

- **Host bridge**: `runAgent()` → `Promise` with 90s timeout
- **Worker**: `START_LOOP` → `runPythonAsync` → await agent response
- **Worker**: `AGENT_COMPLETE`/`AGENT_ERROR` → resolve Host Promise
- **Worker `onerror`**: Reject pending Host requests
- **Worker `onmessageerror`**: Reject pending Host requests

## Verification checklist (non-negotiable)

- [ ] `uv run pytest tests/ -v` passes
- [ ] `node --check` passes on all JS files
- [ ] Server responds with COOP/COEP headers
- [ ] **Drove the browser end-to-end** — clicked Run Agent and saw final answer in UI
- [ ] Console has no red errors after a full run
- [ ] Timeout fires within 90s if broken (not silent hang)

Always perform end-to-end browser testing — curl and pytest are necessary but not sufficient for browser-native apps with runtime errors.