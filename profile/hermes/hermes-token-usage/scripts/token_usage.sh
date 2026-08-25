#!/usr/bin/env bash
# token_usage.sh [HOURS]  — print Hermes model-wise token/cost report for the last HOURS (default 16).
# Reads ~/.hermes/state.db (read-only). No writes.
set -euo pipefail
HOURS="${1:-16}"
DB="${HERMES_STATE_DB:-$HOME/.hermes/state.db}"
if [[ ! -f "$DB" ]]; then echo "state.db not found at $DB" >&2; exit 1; fi
echo "=== Hermes token usage: last ${HOURS}h (from $(date -r "$(sqlite3 "$DB" "SELECT strftime('%s','now')-${HOURS}*3600;")" '+%Y-%m-%d %H:%M' 2>/dev/null || echo 'window')) ==="
sqlite3 -header -column "$DB" <<SQL
SELECT model, billing_provider,
       SUM(api_call_count)     AS calls,
       SUM(input_tokens)       AS input,
       SUM(output_tokens)      AS output,
       SUM(cache_read_tokens)  AS cache_read,
       SUM(reasoning_tokens)   AS reasoning,
       ROUND(SUM(estimated_cost_usd),4) AS est_cost
FROM session_model_usage
WHERE last_seen >= strftime('%s','now') - ${HOURS}*3600
GROUP BY model, billing_provider
ORDER BY input DESC;
SQL
echo ""
echo "=== activity cross-check (messages in window) ==="
sqlite3 -header -column "$DB" <<SQL
SELECT m.session_id, s.model, COUNT(*) AS msgs,
       MAX(datetime(m.timestamp,'unixepoch','localtime')) AS last_msg
FROM messages m JOIN sessions s ON s.id=m.session_id
WHERE m.timestamp >= strftime('%s','now') - ${HOURS}*3600
GROUP BY m.session_id ORDER BY last_msg;
SQL
