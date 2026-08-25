---
name: hermes-token-usage
description: "Query Hermes's token, cost, and model-usage telemetry. Two paths: SQLite state.db for historical/model-wise reports, and live gateway RPC (session.usage, session.context_breakdown, usage.bars) for real-time in-app widgets. Use for any usage report, token count, cost breakdown, or building a live usage UI."
---

# Hermes Token & Usage Reporting

**Two paths — pick based on the task:**

| You need... | Use | Section |
|---|---|---|
| Historical report (last N hours/days), model-wise breakdown, cost stats | **SQLite** `state.db` | Data source ↓ |
| Live per-session token counts (desktop plugin, TUI widget, real-time UI) | **Gateway RPC** `session.usage` | Live runtime RPC ↓ |
| Full RPC method catalog + REST endpoints | `references/gateway-rpc-methods.md` | |

Hermes records all provider token/cost telemetry in a local SQLite database — NOT in logs and NOT in the `messages` table. To report usage you query `state.db`.

## Data source
- **Path:** `~/.hermes/state.db` (SQLite3; `sqlite3` CLI is preinstalled on macOS).
- **Per-profile / per-install.** Each Hermes desktop install or profile has its own `state.db`. Usage done on another device, another profile, or directly on a provider's web dashboard (openrouter.ai, z.ai, deepseek, etc.) will NOT appear here. If the user insists they used more models than the DB shows, ask where (see Pitfalls) — never fabricate.
- The DB is live (WAL). Reads are safe; never write to it. Reads are fast even at 10s of MB.

## The tables that matter

### `session_model_usage`  ← PRIMARY source for model-wise breakdowns
One row per (session, model, billing_provider, billing_base_url, billing_mode). Columns:
`api_call_count, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, estimated_cost_usd, actual_cost_usd, cost_status, cost_source, first_seen, last_seen`.
- **`last_seen` / `first_seen`** are REAL epoch seconds = the actual API activity times. Filter on these for time windows.

### `sessions`  ← per-session rollup, also has `model` + token columns
Columns include `model, billing_provider, started_at, ended_at, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, api_call_count, estimated_cost_usd, actual_cost_usd`.
- `started_at` / `ended_at` are epoch seconds. **`ended_at` today does NOT mean usage happened today** (see Pitfalls).

### `messages`  ← has NO `model` column
Only `role, timestamp, token_count, content, ...`. Use it ONLY to verify *when* activity occurred (`timestamp`), never to attribute tokens to a model. Joining tokens→model via `messages` silently under/over-counts.

## Core workflow
1. **Confirm the right `state.db`.** If multi-device/profile, get the path from the user. Default `~/.hermes/state.db`.
2. **Run the windowed model-wise aggregation** from `session_model_usage` (filter on `last_seen`). → `references/schema-and-queries.md` for SQL, `scripts/token_usage.sh <hours>` for a one-shot report.
3. **Cross-validate** against `sessions` (started/ended) and `messages.timestamp` for the same window — proves the activity actually fell in-window.
4. **Separate free/unknown-cost rows** (`cost_status='unknown'`, `$0.00`) from billed ones. Don't claim a real dollar cost for `:free`/unknown rows.
5. **Present a model-wise table:** model | provider | calls | input | output | cache_read | reasoning | cost.

## Pitfalls (this is where naive reports go wrong)
- **Model-wise data is in `session_model_usage`, NOT `messages`.** `messages` lacks a model column. Always aggregate from `session_model_usage`.
- **`ended_at` today ≠ usage today.** A session can show `ended_at` inside your window while its `session_model_usage.last_seen` (and message timestamps) are weeks old — that's a no-op close, 0 tokens in-window. Filter on real activity time (`last_seen` / `messages.timestamp`), not just `started_at`/`ended_at`.
- **Cache reads dominate and are cheap.** `cache_read_tokens` is usually far larger than `input_tokens`; report them separately so totals/costs look sensible.
- **Free models = $0.00, `cost_status='unknown'`.** Don't assert a dollar figure for `:free` or unknown rows.
- **Per-profile blind spot.** Token stats are per `state.db`. If totals look too low vs. what the user remembers, the rest is in another profile/device DB or a provider dashboard — clarify, never invent models.
- **Anchor the window correctly.** "Last 16 hours" ≠ "today". Use rolling `now - N*3600` for relative windows, or `strftime('%s','YYYY-MM-DD 00:00:00','localtime')` for calendar days. Mind timezone — `localtime` modifier applies local TZ.

## Live runtime RPC (in-app, not SQLite)

For **live per-session token counts** (e.g. inside a desktop plugin or a
TUI widget), don't query SQLite — call the gateway RPC method
`session.usage` via `host.request`:

```js
host.request('session.usage', { session_id })
```

Returns the live agent's cumulative session counters:

| Key | Description |
|---|---|
| `input` | Cumulative session input tokens |
| `output` | Cumulative session output tokens |
| `reasoning` | Cumulative reasoning tokens |
| `total` | `input + output` |
| `calls` | API call count |
| `context_used` | Current context-window occupancy (tokens) |
| `context_max` | Context-window limit (tokens) |
| `context_percent` | `context_used / context_max * 100` |
| `compressions` | Context-compression count (if applicable) |
| `active_subagents` | Background subagents still running |
| `model` | Model slug |

Returns `{calls:0, input:0, output:0, total:0}` for an agent-less session.
No side effects — safe to poll every few seconds.

Other usage-related RPC methods:
- `session.context_breakdown` — `{ session_id }` → per-category context
  allocation (system prompt, tools, history, etc.) + `context_max`/`percent`.
- `usage.bars` → Nous Portal dollar-usage model (two-bar view). Fail-open:
  `{ok:true, available:false}` when logged out.
- `insights.get` → `{ days }` → session/message counts for the period.

REST endpoints (dashboard only, not RPC):
- `GET /api/analytics/usage?days=30` → daily + per-model + totals +
  skills/tools breakdown.
- `GET /api/system/stats` → system-level stats.
- `GET /api/sessions/{id}` → full session row (includes token columns).

## Verification
- Re-run the same aggregation twice (`session_model_usage` vs `sessions`) and confirm they reconcile for in-window sessions.
- Sanity: `SUM(api_call_count)` from `session_model_usage` for the window should roughly match the visible `messages` count for those sessions.

## Support files
- `references/gateway-rpc-methods.md` — full catalog of usage/session RPC methods (`session.usage`, `session.context_breakdown`, `usage.bars`, `insights.get`, `session.list`) and REST endpoints, with response shapes.
- `references/schema-and-queries.md` — full table schemas + copy-paste SQL (rolling window, calendar day, all-time, activity proof).
- `scripts/token_usage.sh` — `token_usage.sh [hours]` prints the model-wise report directly from `state.db`.
