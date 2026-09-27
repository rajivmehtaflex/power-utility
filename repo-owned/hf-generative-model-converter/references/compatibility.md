# Compatibility matrix — hf-generative-model-converter

Statuses per the plan's evidence states: `verified` requires locally executed evidence recorded under
`docs/superpowers/verification/hf-converter/`; `pending` means a concrete pinned procedure exists but has
not yet passed locally; `blocked` names the specific obstacle; `planned` means a future round owns it.
**Nothing on this page counts as supported until it is `verified` here.** Every row names its evidence.

Scope note: this round executes the **GGUF** target only. ONNX and LiteRT-LM are planned rows owned by
plan phase P5 (deferred by project decision, 2026-09-27) and are intentionally *not* advertised by
`SKILL.md` or `assets/recipes.json` until they carry their own verified evidence.

## Text generation — decoder-only

| Source model (pinned) | Target | Exporter / runtime | Platform | Status | Evidence |
|---|---|---|---|---|---|
| `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca` | `gguf` | llama.cpp `convert_hf_to_gguf.py` @ `v0.5.0` (`d2e54583c7452353eb35d40431281f6ee984332f`) + `llama-cli` runtime, source-built | linux-x86_64, CPU | **pending build → verification** | recipe `gguf-qwen3-0.6b-linux-x64-cpu` in `assets/recipes.json`; upstream declares qwen3 conversion support at this pin — to be confirmed at source checkout before any conversion |
| `Qwen/Qwen3-0.6B` @ same | `onnx` | Optimum ONNX + matched `ORTModelForCausalLM` | linux-x86_64, CPU | planned (P5, deferred) | none yet |
| `Qwen/Qwen3-0.6B` @ same | `litert-lm` | `litert_torch` export + LiteRT-LM runtime | linux-x86_64, CPU | planned (P5, deferred; transitive-binary audit outstanding) | none yet |

## Vision-language (image + text → text)

| Source model | Target | Exporter / runtime | Platform | Status | Evidence |
|---|---|---|---|---|---|
| `HuggingFaceTB/SmolVLM-256M-Instruct` (revision unresolved) | `gguf` | multimodal converter + mmproj/runtime pair at llama.cpp pin | linux-x86_64, CPU | pending support check (second pass; no route assumed) | none yet |
| `HuggingFaceTB/SmolVLM-256M-Instruct` | `onnx` / `litert-lm` | — | — | planned (P5) / no assumed route | none yet |
| `google/gemma-3-4b-it` | any | — | — | not pursued (gated source; alternative row only if the primary tuple blocks) | none yet |

## Encoder-decoder (e.g. T5 family)

| Source | Target | Status | Evidence |
|---|---|---|---|
| T5-family (specific model/revision unresolved) | `gguf` | documented-only; upstream support must be checked per model; no promise | none |
| T5-family | `onnx` | planned (P5; separate seq2seq exporter + `ORTModelForSeq2SeqLM` route) | none |

## Runtime-level notes

- GGUF runtime executes on CPU for this baseline. Accelerator backends (CUDA/Metal/Vulkan) are **unverified** on this host and are never claimed by the skill; enabling them is a separate recipe with its own build evidence.
- A host build here does not establish Android, browser, mobile, or other-host artifact compatibility; deployment targets are recorded per recipe and separately verified.
