# Chainlit Launch for FCP Data Processor

This reference documents the specific steps and issues encountered when launching the Chainlit Finance Assistant UI for the FCP Data Processor project.

## Project Context

- **Project**: FCP Data Processor (`/Users/rajivmehtapy/Documents/fcp-data-processor`)
- **Service**: `service/g-fcp-da-chainlit` (Chainlit Finance Assistant)
- **Default Port**: 8001 (changed from 8000)
- **Environment**: macOS, Python 3.12, `uv` package manager

## Session Timeline & Issues

### 1. Initial Attempt (Port 8001)
```bash
cd /Users/rajivmehtapy/Documents/fcp-data-processor/service/g-fcp-da-chainlit
CHAINLIT_PORT=8001 uv run chainlit run app.py --port 8001
```
**Result**: Failed - `chainlit` command not found in PATH.

### 2. Dependency Installation
```bash
uv sync  # Installed chainlit and dependencies
uv pip install greenlet  # Required for SQLAlchemy async
```

### 3. Port Conflict Resolution
Multiple attempts to start on port 8001 failed with "address already in use":
```bash
# Found PIDs using port 8001
lsof -ti:8001  # Returned 21524, 22647, 22730, 83139

# Killed processes
kill -9 21524 22647 22730 83139
# Or: pkill -f "chainlit run app.py"
```

### 4. Successful Launch
```bash
cd /Users/rajivmehtapy/Documents/fcp-data-processor/service/g-fcp-da-chainlit
.venv/bin/python -m chainlit run app.py --port 8001
```
**Result**: Success - "Your app is available at http://localhost:8001"

## Key Configuration Files

### `.env` (in service/g-fcp-da-chainlit/)
```bash
OPENROUTER_API_KEY=sk-or-...3ca7
CHAINLIT_AUTH_SECRET=d1f3b23d1018c362bb929502c5e2e07717962672ea18ce3e200710637063e882
AUTH_USERS=admin:root123_
ORCHESTRATOR_MODEL=openrouter:openrouter/free
FALLBACK_MODEL=openrouter:google/gemini-3.1-flash-lite-preview
SWOT_SYNTHESIS_MODEL=openrouter:openai/gpt-5.6-luna
SWOT_FALLBACK_MODEL=openrouter:openai/gpt-5.6-luna
LOG_FILE_PATH=logs/agent_flow.log
XERO_DUCKDB_PATH=/Users/rajivmehtapy/Documents/fcp-data-processor/service/g-data-xero-api/data/xero.duckdb
HERMES_API_URL=http://127.0.0.1:8642/v1
HERMES_API_KEY=719431f1fa16beb101de0e528ae4c3f9316096f616fdd77a0a0a308630a0ca7b
AGENT_BACKEND=hermes
```

### `.env.example` (template)
```bash
OPENROUTER_API_KEY=your_api_key_here
CHAINLIT_AUTH_SECRET=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
AUTH_USERS=alice:mypassword,bob:otherpass
ORCHESTRATOR_MODEL=openrouter:anthropic/claude-3.5-sonnet
FALLBACK_MODEL=openrouter:google/gemini-3.1-flash-lite-preview
MAX_TOKENS=4096
SWOT_SYNTHESIS_MODEL=openrouter:~anthropic/claude-haiku-latest|openrouter:deepseek/deepseek-r1|openrouter:openai/o3-mini|openrouter:qwen/qwen3.6-plus
SWOT_FALLBACK_MODEL=openrouter:deepseek/deepseek-r1
LOG_FILE_PATH=logs/agent_flow.log
XERO_DUCKDB_PATH=/path/to/service/g-data-xero-api/xero_accounts.duckdb
```

## Log Files

| Log File | Purpose |
|----------|---------|
| `logs/chainlit.log` | Chainlit server startup and HTTP requests |
| `logs/agent_flow.log` | Agent queries, model calls, errors |
| `logs/app_events.log` | Chainlit event lifecycle (chat_start, chat_resume, etc.) |
| `logs/init_db.log` | Database bootstrap (init_db.py) |

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `chainlit: command not found` | Not in PATH, not installed | `uv sync` or `uv pip install chainlit` |
| `Address already in use` | Previous process didn't clean up | `pkill -f "chainlit run app.py"` then restart |
| `No module named 'greenlet'` | Missing SQLAlchemy dependency | `uv pip install greenlet` |
| `Status 403: Model only available in US` | Geo-restriction on model | Use US-accessible models (openrouter/free, google/gemini) |
| `Could not read report_trial_balance` | DuckDB views not initialized | Run `python init_db.py` |

## Verification Commands

```bash
# Check process is running
lsof -i :8001

# Check HTTP response
curl -s http://localhost:8001 | grep -i "Assistant"

# Tail logs in real-time
tail -f logs/chainlit.log
tail -f logs/agent_flow.log
```

## Access

- **URL**: http://localhost:8001
- **Username**: admin
- **Password**: root123_ (from `.env` `AUTH_USERS`)

## Related Files

- `service/g-fcp-da-chainlit/app.py` - Main Chainlit application
- `service/g-fcp-da-chainlit/init_db.py` - Database bootstrap
- `service/g-fcp-da-chainlit/finance_agent/agent.py` - Agent logic
- `service/g-fcp-da-chainlit/finance_agent/AGENTS.md` - Agent system prompt