# Managed agents & exact-request control: `agent run`

`agent run` is the escalation path when intent commands (`generate`, `image`, …)
aren't enough: managed agents, background execution, and exact request bodies.

## One-shot model call with full control

```bash
gemini-api agent run "Explain concurrency in one sentence" --model gemini-3.8-flash
gemini-api agent run --body @request.json          # exact JSON body
gemini-api agent run --schema                      # print the request body JSON Schema
```

`--body` merges with intent inputs and rejects duplicate keys; `@path` reads a
file, `@-` reads stdin to EOF. Variant flags (`--agent` vs `--model`) cannot be
combined.

## Background runs — don't block the calling agent

Managed agents (Deep Research, Antigravity) provision a sandbox and can run for
minutes. The pattern:

```bash
# 1. Start in the background; capture only the interaction ID
ID=$(gemini-api agent run "Research solar battery recycling, cite sources" \
      --agent deep-research-preview-04-2026 \
      --background --stream=false \
      --output-format json --jq '.id')

# 2. Later: poll status / fetch the finished output
gemini-api agent status "$ID" --output-format json
gemini-api agent status "$ID" --jq '.output_text'   # final report text
```

- `--background` returns immediately with an interaction ID.
- `agent status` retrieves state or replays the stream (`--stream`).
- Discover available managed agents: `gemini-api agent list`.

## Multi-turn: two independent state handles

- Conversation context (history, reasoning) → `--previous-interaction-id`
- Sandbox/environment state (files, installed packages) → environment ID
  (see `agent status` output); these resume independently.

## Escalation ladder

1. Intent command (`generate`, `analyze`, …) — simplest, try first.
2. `agent run --model ...` — same request space, more flags.
3. `agent run --body @req.json` — exact bytes; build the body after checking
   `--schema`, and validate with `--dry-run` before sending.

## Related management commands

- `gemini-api agent list` — managed agents available to you
- `gemini-api triggers` — schedule agents on cron schedules
- `gemini-api environments` — inspect sandbox environments and their files
- `gemini-api webhooks` — webhook endpoints and signing secrets for events

## Gotchas

- Long background runs: poll `agent status`, don't spin in a tight loop
  (`--background` + a sleep or later check is the intended flow).
- **Retrieval gotcha:** for some managed agents (observed with
  deep-research-preview-*), `agent status --jq '.output_text'` returns `null`
  even after completion — the report text and figures live under
  `.steps[].content[]` (`type=text` parts in step order; `type=image` parts are
  base64 figures). When the obvious field comes back empty, fetch the full
  status JSON once (`--output-format json`) and inspect its structure.
- `--agent` and `--model` are mutually exclusive variants; mixing them is an
  exit-2 usage error.

Full flags: `gemini-api agent run --help` / `agent status --help` ·
docs: https://ai.google.dev/gemini-api/docs/managed-agents-quickstart
