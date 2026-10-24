# Text generation with `gemini-api generate`

Send a prompt to a Gemini model and stream the reply to stdout. This is the
workhorse for second opinions, explanations, reviews, drafting, and any
"text in → text out" task where the calling agent stays in control of context.

## When to use `generate` vs `agent run`

`generate` is the simple intent: one prompt, one reply, streaming by default.
Reach for `agent run` (see [managed-agents.md](managed-agents.md)) only when you
need a managed agent, background execution, or an exact `--body` JSON request.

## Quick reference

```bash
gemini-api generate "Explain the CAP theorem in one sentence"
gemini-api generate "Review this code for bugs" -i src/auth.go          # attach a file
gemini-api generate "Compare these two screenshots" -i a.png -i b.png
gemini-api generate "Summarize the video" -i https://youtu.be/dQw4w9WgXcQ
gemini-api generate "Be terse" --system "You are a laconic senior engineer."
gemini-api generate "Continue this" --previous-interaction-id v1_...    # multi-turn
```

Key flags: `-m/--model` (default gemini-3.8-flash) · `-i/--input` (repeatable:
local path, `files/<id>`, or YouTube URL) · `--system` (system instruction) ·
`--previous-interaction-id` (continue an earlier interaction) · `--stream=false`
(one complete result instead of streamed deltas) · `--body @req.json` (exact
request JSON; get the shape with `--schema`).

## Agent patterns

- **Extract a field, not prose:** `gemini-api generate "List the 3 risks as JSON
  array" --stream=false --output-format json --jq '[.[] | .risk]'`
- **Big prompt from a file or stdin:** `--stdin` reads prompt text to EOF;
  `--body @path` reads a full JSON request from a file.
- **Thinking models may stream in a burst.** High-reasoning models (e.g.
  gemini-3.8-flash) can emit deltas all at once after internal thinking; that's
  expected, not a hang. Use `--stream=false` when you want exactly one result.
- **Multi-turn:** capture the interaction ID from the JSON output of turn one
  (`--output-format json`), then pass `--previous-interaction-id` on turn two.

## Gotchas

- The 20 MB inline request limit applies (see [files-models-auth.md](files-models-auth.md)).
- Wrong flag names exit with code `2` — check `gemini-api generate --help`
  rather than guessing; the help text lists every live flag.
- Exit code `3` is an auth problem; no retry will fix it.

Full flag set: `gemini-api generate --help` · request body shape: `--schema` ·
upstream docs: https://ai.google.dev/gemini-api/docs/text-generation
