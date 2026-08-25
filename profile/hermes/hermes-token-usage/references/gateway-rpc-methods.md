# Gateway RPC Methods for Usage & Session Data

Complete catalog of gateway JSON-RPC methods (called via `host.request(method, params)`)
related to token usage, session data, and analytics. Verified from
`tui_gateway/methods_session.py` and `tui_gateway/methods_tools.py` source.

## session.usage

```js
host.request('session.usage', { session_id })
```

Live per-session token/cost counters from the running agent. Returns:

```json
{
  "model": "glm-5.2",
  "input": 45000,
  "output": 12000,
  "reasoning": 3000,
  "prompt": 45000,
  "completion": 12000,
  "total": 57000,
  "calls": 15,
  "context_used": 42000,
  "context_max": 128000,
  "context_percent": 33,
  "compressions": 0,
  "active_subagents": 2
}
```

Returns `{calls:0, input:0, output:0, total:0}` for an agent-less session.
Read-only, no side effects — safe to poll every few seconds.
Source: `tui_gateway/methods_session.py` `@method("session.usage")`.

## session.context_breakdown

```js
host.request('session.context_breakdown', { session_id })
```

Per-category context allocation (system prompt, tools, history, etc.):

```json
{
  "categories": [
    { "id": "system_prompt", "label": "System Prompt", "tokens": 5000 },
    { "id": "tools", "label": "Tools", "tokens": 3000 },
    ...
  ],
  "context_max": 128000,
  "context_percent": 33,
  "context_used": 42000,
  "estimated_total": 42000,
  "model": "glm-5.2"
}
```

Source: `tui_gateway/methods_session.py` `@method("session.context_breakdown")`.

## usage.bars

```js
host.request('usage.bars')
```

Nous Portal dollar-usage model (two-bar view). Fail-open:
`{ok:true, available:false}` when logged out or portal unreachable.
Source: `tui_gateway/methods_session.py` `@method("usage.bars")`.

## insights.get

```js
host.request('insights.get', { days: 30 })
```

Aggregated session/message counts for the period:

```json
{
  "days": 30,
  "sessions": 45,
  "messages": 1200
}
```

Source: `tui_gateway/methods_tools.py` `@method("insights.get")`.

## session.list

```js
host.request('session.list', { limit: 200 })
```

Recent sessions (deny-lists `tool` source). Returns only summary fields:
`id, title, preview, started_at, message_count, source`. **No token data** —
use `session.usage` or SQLite for token counts.
Source: `tui_gateway/methods_session.py` `@method("session.list")`.

## session.status

```js
host.request('session.status', { session_id })
```

Session lifecycle status. Source: `tui_gateway/methods_session.py`.

## REST endpoints (dashboard only — NOT accessible via host.request)

These are HTTP routes served by the web dashboard, not JSON-RPC methods:

- `GET /api/analytics/usage?days=30` — daily + per-model token/cost/session
  breakdown + skills/tools. Backed by `_get_usage_analytics()` in
  `hermes_cli/web_server.py`.
- `GET /api/sessions/{id}` — full session row including all token columns
  (`input_tokens, output_tokens, cache_read_tokens, reasoning_tokens,
  estimated_cost_usd, actual_cost_usd, api_call_count`).
- `GET /api/sessions/stats` — `total, active_store, archived, messages,
  by_source` counts.
- `GET /api/system/stats` — system-level stats.

To access REST from a plugin: use `ctx.rest()` (scoped to plugin namespace)
or ship a Python `plugin_api.py` backend. For gateway-wide data, use
`host.request` with the RPC methods above instead.
