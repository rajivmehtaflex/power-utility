# Hermes Token Usage — Schema & Ready SQL

DB: `~/.hermes/state.db` (SQLite3). Read-only. Epoch-seconds columns use REAL; convert with
`datetime(epoch,'unixepoch','localtime')`. `now` via `strftime('%s','now')`.

## Tables & key columns

`sessions` (one row per chat session)
- `id PK, model, billing_provider, started_at REAL, ended_at REAL,`
- `input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens,`
- `api_call_count, estimated_cost_usd, actual_cost_usd, cost_status, cost_source`

`session_model_usage` (PRIMARY source for model-wise stats; one row per session×model×provider)
- `session_id FK, model, billing_provider,`
- `api_call_count, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,`
- `reasoning_tokens, estimated_cost_usd, actual_cost_usd, cost_status, cost_source,`
- `first_seen REAL, last_seen REAL`  ← use these for time windows
- PK: (session_id, model, billing_provider, billing_base_url, billing_mode)

`messages` (NO model column; only verify activity timing)
- `session_id FK, role, timestamp REAL, token_count, content, ...`

## Queries

### 1. Model-wise breakdown — LAST N HOURS (rolling)
Replace `16` with the window in hours:
```sql
SELECT model, billing_provider,
       SUM(api_call_count)            AS calls,
       SUM(input_tokens)              AS input,
       SUM(output_tokens)             AS output,
       SUM(cache_read_tokens)         AS cache_read,
       SUM(reasoning_tokens)          AS reasoning,
       ROUND(SUM(estimated_cost_usd),4) AS est_cost,
       ROUND(SUM(actual_cost_usd),4)  AS act_cost
FROM session_model_usage
WHERE last_seen >= strftime('%s','now') - 16*3600
GROUP BY model, billing_provider
ORDER BY input DESC;
```

### 2. Model-wise breakdown — CALENDAR DAY (today)
```sql
SELECT model, billing_provider,
       SUM(api_call_count) AS calls, SUM(input_tokens) AS input,
       SUM(output_tokens) AS output, SUM(cache_read_tokens) AS cache_read,
       SUM(reasoning_tokens) AS reasoning
FROM session_model_usage
WHERE last_seen >= strftime('%s','2026-07-15 00:00:00','localtime')
GROUP BY model, billing_provider
ORDER BY input DESC;
```

### 3. Prove activity actually fell in-window (cross-check, avoids the ended_at trap)
```sql
SELECT m.session_id, s.model, COUNT(*) AS msgs,
       MIN(datetime(m.timestamp,'unixepoch','localtime')) AS first,
       MAX(datetime(m.timestamp,'unixepoch','localtime')) AS last
FROM messages m JOIN sessions s ON s.id=m.session_id
WHERE m.timestamp >= strftime('%s','now') - 16*3600
GROUP BY m.session_id ORDER BY last;
```

### 4. Sessions started/ended in window (sanity, but remember ended≠usage)
```sql
SELECT id, model, billing_provider,
       datetime(started_at,'unixepoch','localtime') AS started,
       datetime(COALESCE(ended_at,started_at),'unixepoch','localtime') AS ended,
       input_tokens, output_tokens, api_call_count
FROM sessions
WHERE started_at >= strftime('%s','now') - 16*3600
   OR (ended_at IS NOT NULL AND ended_at >= strftime('%s','now') - 16*3600)
ORDER BY started_at;
```

### 5. All-time models (for reconciliation / "what have I used")
```sql
SELECT model, billing_provider, COUNT(*) n,
       SUM(input_tokens) in_tok, SUM(output_tokens) out_tok
FROM sessions WHERE model IS NOT NULL
GROUP BY model, billing_provider ORDER BY n DESC;
```

## Gotchas observed
- `session_model_usage` may have far fewer rows than `sessions` (only sessions that actually
  hit an API). Aggregate from it for model stats; use `sessions` only for session-level rollups.
- `cost_status='unknown'` + `$0.00` = free/`:free` model — do not print a fake dollar cost.
- `messages` has no model column; never derive model usage from it.
