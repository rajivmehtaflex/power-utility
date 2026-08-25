# OpenRouter Model Resolution — Code Path Trace & Empirical Transcript

Captured 2026-07-14 while answering "how do I add a model to OpenRouter provider
in Hermes". Goal: explain why a model isn't in the picker but can still be used,
with the exact source-level mechanism and a reproducible validation test.

## The two systems

### 1. Picker (curated subset only)
- `hermes_cli/models.py::OPENROUTER_MODELS` — hand-picked tuple `(model_id, desc)`
  (~50 entries: Anthropic, OpenAI, Google, xAI, DeepSeek, Qwen, Moonshot, MiniMax,
  Z-AI, Xiaomi, Tencent, StepFun, NVIDIA, Sakana, OpenRouter routers, free-tier).
- `fetch_openrouter_models(timeout, force_refresh)`:
  - Prefers remote `model_catalog.json` via `get_curated_openrouter_models()`
    (from `hermes_cli/model_catalog.py`), falls back to `OPENROUTER_MODELS`.
  - Then intersects with the live `https://openrouter.ai/api/v1/models` catalog,
    hiding any model whose `supported_parameters` explicitly omits `tools`
    (agent requires tool-calling; missing field = permissive/allowed).
  - Marks `curated[0]` as "recommended".
- `hermes_cli/inventory.py::build_models_payload()` turns these into picker rows.
- `cli.py::_handle_model_picker_selection()` renders provider → model stages.
  **No free-text "type a custom ID" field exists** in the interactive picker.

### 2. Runtime validation (accepts any real model)
- `validate_requested_model(model_name, provider, api_key, base_url, api_mode)`:
  - `normalized = openrouter` (unless `base_url` lacks `openrouter.ai` → `custom`).
  - Calls `fetch_api_models(api_key, base_url)` → probes live `/v1/models`.
  - If `requested_for_lookup in set(api_models)` → `accepted=True, recognized=True, persist=True`.
  - Else: if it matches the curated catalog (`_model_in_provider_catalog`) → accept.
    Else → `accepted=False` with suggestions (unless `/models` unreachable → warn-but-accept).
- `switch_model()` in `hermes_cli/model_switch.py` actually applies the change.

Conclusion: **picker visibility ≠ runtime availability.** The picker list is a
convenience; the live `/v1/models` probe is the source of truth for whether a
model runs.

## Empirical transcript (reproduce with the recipe in SKILL.md)

```
$ cd ~/.hermes/hermes-agent && ./venv/bin/python -c "...validate_requested_model..."
google/gemini-2.5-pro              -> accepted=True  recognized=True  persist=True
anthropic/claude-3.5-sonnet        -> accepted=False recognized=False persist=False
   msg: Model `anthropic/claude-3.5-sonnet` was not found in this provider's model listing.
   Similar models: `anthropic/claude-sonnet-5`, `anthropic/claude-sonnet-4`, ...
meta-llama/llama-3.1-8b-instruct   -> accepted=True  recognized=True  persist=True
```

Interpretation:
- `gemini-2.5-pro` and `llama-3.1-8b-instruct` are NOT in the curated picker list
  but ARE accepted by the runtime — confirming the gap.
- `claude-3.5-sonnet` returns `accepted=False` because OpenRouter retired it —
  proving the probe is live, not a rubber stamp. User should confirm the current
  ID on https://openrouter.ai/models.

## Why OpenRouter is the easiest provider to add arbitrary models to
OpenRouter is a routing aggregator. `provider_model_ids('openrouter')` returns
`model_ids()` → `fetch_openrouter_models()`, and `validate_requested_model`
passes any valid upstream ID through (no family-prefix gate, no catalog-only
fallback rejection). Contrast with `openai-codex`/`xai-oauth`, which enforce a
plausibility gate (only `gpt-*`/`grok-*` accepted softly) — those reject
unrelated IDs outright.

## Quick reference: commands that change the default model
- `/model <id>` in chat — persists by default (config `model.persist_switch_by_default`, default True).
- `/model <id> --session` — current session only.
- `/model <id> --global` — explicit persist.
- `/model <id> --provider openrouter` — pin provider.
- `hermes config set model.default "<id>"` and `hermes config set model.provider "openrouter"` — config-level, no picker/session.
- `hermes model --refresh` — wipes the on-disk picker cache (`~/.hermes/cache/model_catalog.json`) and re-fetches the remote catalog. Only affects picker *visibility*.
