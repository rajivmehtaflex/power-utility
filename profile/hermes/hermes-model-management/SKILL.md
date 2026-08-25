---
name: hermes-model-management
description: "Add, find, and use models in Hermes that are NOT in the interactive provider picker (OpenRouter especially, but applies to any provider). Covers the critical picker-vs-runtime gap: the picker shows a curated subset while the runtime accepts any valid model ID."
license: MIT
metadata:
  author: Hermes Agent
  platforms: linux, macos, windows
  version: 1.0.0
---

# Hermes Model Management — Using Models the Picker Doesn't Show

The single most common "I can't find my model" confusion in Hermes comes from a
mismatch between two systems:

1. **The picker** (`/model`, `hermes model`, the GUI/dashboard model selector)
   shows a **curated subset** of each provider's catalog — not the full catalog.
2. **The runtime** (`validate_requested_model` + `switch_model`) accepts **any
   real, tool-capable model ID** that exists on the provider's live `/v1/models`
   endpoint — regardless of whether it appears in the picker.

So a model "missing" from the picker is almost never actually unusable. You just
have to select it by typing the exact ID rather than clicking it, or set it in
config directly.

## Trigger conditions

Use this skill when the user says things like:
- "I can't find my model in the picker / model list"
- "How do I add a model to provider X (OpenRouter, Nous, etc.)"
- "The model I want isn't listed when I run `hermes model`"
- "Add more models to OpenRouter"
- Wants to use a specific model ID that isn't surfaced by the CLI/GUI picker

## Core mental model

For OpenRouter (an aggregator), `hermes_cli/models.py` defines:
- `OPENROUTER_MODELS` — a hand-picked ~50-entry tuple that drives the picker.
- `fetch_openrouter_models()` — merges that with a remotely-hosted
  `model-catalog.json` (fetched hourly from `hermes-agent.nousresearch.com/docs/api/model-catalog.json`,
  with a `raw.githubusercontent.com/NousResearch/hermes-agent/main/website/static/api/model-catalog.json` fallback).
- The picker only renders what these two sources produce. OpenRouter itself has 200+ models.

But `validate_requested_model()` (same file) probes the live `https://openrouter.ai/api/v1/models`
endpoint. If the typed ID exists there and advertises tool support, it returns
`accepted=True, recognized=True, persist=True`. The picker list is irrelevant to
whether the model actually runs.

## Three ways to use a model that isn't in the picker

**Method 1 — Type the exact ID directly (validated live; recommended)**
- In chat: `/model <exact-openrouter-id>` — e.g. `/model openai/gpt-4o-mini`.
- Flags: `--session` (one-off, don't persist), `--global` (persist explicitly),
  `--provider <slug>` to pin the provider.
- CLI one-shot: `hermes chat -m openai/gpt-4o-mini -q "..."`
- Works for ANY real OpenRouter model ID, even ones not in the curated list.

**Method 2 — Set config directly (bypasses picker AND validation)**
```bash
# Shorthand format (auto-sets provider):
hermes config set model.default "openrouter/google/gemma-2-9b-it"

# Explicit format:
hermes config set model.default "google/gemma-2-9b-it"
hermes config set model.provider openrouter
```
- OpenRouter passes any valid ID straight through to the upstream provider.
- Persists to `~/.hermes/config.yaml`. Survives restarts. No picker needed.
- Use this when you want a non-curated model as the default without typing it each time.

See `references/config-model-setting.md` for shorthand format details and common OpenRouter free models.

**Method 3 — Add it to the curated picker list (only if you want it *visible* in `/model`)**
- Edit `OPENROUTER_MODELS` in `hermes_cli/models.py` (or the remote `model-catalog.json`
  manifest). Append a tuple `("vendor/model", "optional description")`.
- Requires modifying Hermes source — only do this if you specifically want the
  model selectable from the picker UI. Methods 1/2 are simpler for just *using* it.
- The interactive `hermes model` picker has **no "type a custom ID" free-text field**,
  so if the goal is picker visibility, editing source is the only path.

## Verification recipe (run before claiming a model works)

You can validate a model ID against the live OpenRouter catalog without a full
Hermes session, using the bundled `hermes_cli.models` module:

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python -c "
import sys; sys.path.insert(0, '.')
from hermes_cli import models
for mid in ['google/gemini-2.5-pro', 'meta-llama/llama-3.1-8b-instruct', 'anthropic/claude-3.5-sonnet']:
    r = models.validate_requested_model(mid, 'openrouter', api_key=None, base_url='https://openrouter.ai/api/v1')
    print(mid, '->', 'accepted=' + str(r.get('accepted')), 'recognized=' + str(r.get('recognized')))
"
```
- `accepted=True` → the model will run; tell the user to use Method 1 or 2.
- `accepted=False` with "not found in this provider's model listing" → the ID is
  wrong/retired/renamed on OpenRouter. Confirm the exact ID at `https://openrouter.ai/models`.
- Note: `anthropic/claude-3.5-sonnet` returns `accepted=False` because OpenRouter
  retired it — proving the check is live, not a rubber stamp.

## Per-provider validation behavior (important nuances)

`validate_requested_model()` logic in `hermes_cli/models.py`:
- **openrouter**: probes live `/v1/models`; accepts any listed, tool-capable model.
  Models whose `supported_parameters` explicitly omits `tools` are hidden (agent
  requires tool-calling). Missing-field models are treated permissively (allowed).
- **openai-codex / xai-oauth**: validated against a curated catalog with a
  *plausibility gate* — only family-matching prefixes (gpt-*, grok-*) are
  soft-accepted; unrelated IDs are rejected with "switch provider" guidance.
- **minimax / minimax-cn / anthropic**: no `/v1/models` path or gated; falls back
  to curated catalog, but still soft-accepts unknown IDs with a warning.
- **custom / custom:<name>**: probes the endpoint's `/models`; if unreachable or
  it's an Anthropic-messages proxy, the model is accepted *without verification*.
- **generic fallback**: if `/models` is unreachable for an unknown provider, the
  model is accepted with a warning ("could not reach API to validate").

Implication: OpenRouter is the easiest provider to add arbitrary models to,
because it's an aggregator with a live, permissive catalog.

## Pitfalls

- **Don't tell the user to edit source first.** The picker gap is the #1 confusion;
  Method 1/2 solves 99% of cases without touching `models.py`.
- **Model names can't contain spaces** — `validate_requested_model` rejects any
  `requested` with whitespace. Always use the exact `vendor/model` slug.
- **Retired/renamed models fail the live check** — that's expected, not a bug.
  Verify the current ID on the provider's site.
- **The hourly `model-catalog.json` cache** can lag new releases; this only
  affects picker *visibility*, never runtime acceptance. Use `hermes model --refresh`
  to force a cache wipe if the picker looks stale, but runtime typos still work
  regardless.
- **Nous Portal free-tier users** see paid models grayed out in the picker
  (`unavailable_models`) — but that's a tier gate, not a missing-model issue.

## Key source files (for deep dives)

- `hermes_cli/models.py` — `OPENROUTER_MODELS`, `fetch_openrouter_models()`,
  `validate_requested_model()`, `provider_model_ids()`.
- `hermes_cli/model_catalog.py` — remote `model-catalog.json` fetch/validate/cache.
- `hermes_cli/inventory.py` — `build_models_payload()` builds the picker rows.
- `cli.py` — `_handle_model_picker_selection()` / `_handle_model_switch()` drive
  the interactive picker and `/model` command.

See `references/openrouter-model-resolution.md` for the full code-path trace and
empirical test transcript behind these findings.

See `references/config-model-setting.md` for shorthand format and common OpenRouter
free model recommendations.
