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
| `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca` | `gguf` | llama.cpp `convert_hf_to_gguf.py` @ `v0.5.0` (`7fe450e19305b828c199d602c23a8337aaa1f03b`) + source-built runtime | linux-x86_64, CPU | **conversion-verified** (2026-09-27): source build, conversion, functional smoke, staged reload, and private publication all passed; numerical parity FAILED at the declared Jaccard-0.5 threshold on 2/3 short fixtures (near-limit fixture matched exactly) and is reported on the model card | recipe `gguf-qwen3-0.6b-linux-x64-cpu` in `assets/recipes.json`; `docs/superpowers/verification/hf-converter/runtime-results.json`; published receipt `rajivmehtapy/test-hf-converter-qwen3-0.6b-gguf` @ `39da3ef8` (private) |
| `Qwen/Qwen3-0.6B` @ same | `onnx` | Optimum ONNX + matched `ORTModelForCausalLM` | linux-x86_64, CPU | planned (P5, deferred) | none yet |
| `Qwen/Qwen3-0.6B` @ same | `litert-lm` | `litert_torch` export + LiteRT-LM runtime | linux-x86_64, CPU | planned (P5, deferred; transitive-binary audit outstanding) | none yet |

## Vision-language (image + text → text)

| Source model | Target | Exporter / runtime | Platform | Status | Evidence |
|---|---|---|---|---|---|
| `HuggingFaceTB/SmolVLM-256M-Instruct` @ `7e3e67edbbed1bf9888184d9df282b700a323964` (Apache-2.0, not gated) | `gguf` | llama.cpp `convert_hf_to_gguf.py` two-run conversion (text model + `--mmproj` projector) @ `v0.5.0` + `llama-mtmd-cli` runtime | linux-x86_64, CPU | **conversion-verified** (2026-09-27): two-image protocol fully passed — reference and converted both answered correctly on both fixtures, converted outputs identical to reference; staged reload and private publication verified (16/16 remote files) | recipe `gguf-smolvlm-256m-linux-x64-cpu`; `runtime-results-vlm.json`; receipt `rajivmehtapy/test-hf-converter-smolvlm-256m-gguf` @ `5aedf072` (private) |
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
