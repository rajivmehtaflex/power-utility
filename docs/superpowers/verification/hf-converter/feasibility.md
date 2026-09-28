# P2 Feasibility — host preflight and revision pins (GGUF round)

Recorded: 2026-09-27. Executor: this session, on the recorded build host.

## Host preflight (build + execution host)

| Check | Observed | Consequence |
|---|---|---|
| OS / arch | Ubuntu 24.04.5 LTS, x86_64 | Build triplet `linux-x86_64`; other hosts unverified |
| CPU | 4 × Intel Xeon @ 2.60 GHz | Build jobs capped at `-j4` |
| Memory | 14,985 MB total / 11,786 MB available | Sequential heavy builds; Qwen3-0.6B (0.6 B params) fits comfortably for convert + CPU inference |
| Disk (project mount) | 333 GB free | Source tree (~1 GB), build tree (~2 GB), model (~1.2 GB BF16), artifacts — ample |
| GPU / accelerator | none (`nvidia-smi` absent) | Execution = CPU only; any accelerator claim stays **unverified** |
| Compiler / build tools | gcc 13.3.0, g++ 13.3.0, make 4.3, cmake 3.28.3, git 2.42.0, curl 8.5.0 | Sufficient for llama.cpp CMake build |
| ccache | absent | Not required; recorded as absent |
| libcurl dev headers | absent → installed `libcurl4-openssl-dev 8.5.0-2ubuntu10.15` via apt | Declared system bootstrap input (allowed class); needed for llama.cpp `LLAMA_CURL=ON` |

**Feasibility decision:** the GGUF CPU route (llama.cpp source build → Qwen3-0.6B conversion → bounded CPU inference) is feasible on this host within budget. Proceed to P4 source build.

## Immutable pins resolved

| Component | Pin | Verification |
|---|---|---|
| llama.cpp | tag `v0.5.0`, commit `7fe450e19305b828c199d602c23a8337aaa1f03b` (release 2026-09-23) | tag object `c13fcbf684171d5e0bca3fc5c34be6a99174b05f` peels to this commit, verified in the local clone; note: the releases API `target_commitish` (`d2e5458…`) is the branch head at publish time and was **not** used as the pin |
| `Qwen/Qwen3-0.6B` | revision `c1899de289a04d12100db370d81485cdf75e47ca` | HF API (`/api/models/Qwen/Qwen3-0.6B`), authenticated read |
| Model facts | `Qwen3ForCausalLM`, `model_type: qwen3`, Apache-2.0, **not gated**, 10 repo files incl. single `model.safetensors` + `tokenizer.json` (fast tokenizer) | same response |
| HF authorization | read token role=`read`, write token role=`write`, user `rajivmehtapy` | `whoami-v2` checked at setup |

## Candidate matrix decisions for this round

- `Qwen3-0.6B` × GGUF: **selected** for the verified text tuple (see `assets/recipes.json`; build/conversion evidence pending until P4/P7).
- `SmolVLM-256M-Instruct` × GGUF (VLM): **pending support check** — requires the multimodal converter/runtime pair at the llama.cpp pin; not assumed. Second pass.
- `gemma-3-4b-it`: not pursued (gated source; alternative-evidence row only if the primary tuple blocks).
- ONNX and LiteRT-LM rows: **parked by scope decision** (plan P5 deferred); recorded in `compatibility.md` as planned-but-unverified, never advertised.
- Encoder-decoder (T5 family): documented-only; no promise this round.

## Open risks carried into P4

1. ~~Qwen3 support in the converter is upstream-declared only.~~ **Resolved at checkout:** the pin
   registers `Qwen3ForCausalLM` via `conversion/qwen.py:159` (`@ModelBase.register("Qwen3ForCausalLM",
   "Qwen3Model")`, model class inheriting `Qwen2Model`); the converter's model registry lives in the
   `conversion/` package at this revision. Confirmed 2026-09-27 in the local pinned checkout.
2. ~~Dependency-lock hash not yet computable.~~ **Resolved:** converter env locked via uv
   (`uv.lock`, sha256 `87ac7a849f8798bd3c584e52d45dbe5eb11be867b5d2da1cf935a5611275ad21`, 31 packages:
   torch 2.11.0+cpu from the declared CPU index, transformers 4.57.6, numpy 2.2.6, protobuf<5,
   huggingface-hub 0.36.2, `gguf` 0.19.0 from the same pinned llama.cpp tree rather than PyPI).
   Build key `198232c63ac3c736` = sha256(llama.cpp commit ‖ build flags ‖ gcc 13.3.0 ‖ cmake 3.28.3 ‖
   dep-lock sha256)[:16].

## ONNX round feasibility — resolved 2026-09-28

- **Qwen3 export support:** confirmed at the resolved pins — `qwen3` is registered for
  `text-generation-with-past` (plus feature-extraction/text-classification variants) via
  `@register_tasks_manager_onnx` in `optimum.exporters.onnx.model_configs` (41 model types support
  the task at optimum-onnx 0.1.0). Probe correction: the tasks mapping reads empty until the config
  module is imported — registration is decorator-driven.
- **Ecosystem split:** `optimum` 2.x is a hardware meta-package; ONNX export lives in
  **`optimum-onnx`** (`optimum-onnx 0.1.0`, requires `optimum~=2.1.0`,
  `transformers>=4.36,<4.58`, `onnxruntime>=1.18`). transformers 4.57.6 and onnxruntime 1.30.0 both
  fit. Matched loading class: `ORTModelForCausalLM`.
- **Runtime decision (user, 2026-09-28):** declared official onnxruntime PyPI wheel instead of a
  multi-hour 4-core source build — recorded provenance (wheel sha256 + installed-native-lib byte
  comparison) keeps the no-silent-prebuilt policy intact; `source-build-verified` is not claimed.
- **VLM ONNX:** deferred by scope decision (2026-09-28) — no exporter/loader feasibility claimed.
- **Discovered constraint carried into the recipe:** optimum 2.1.0 ignores qwen3's explicit
  `head_dim` when sizing the KV cache (uses `hidden_size//num_heads`); the exported graph is
  correct and a declared one-attribute load patch is required at inference.

## LiteRT-LM round feasibility — recon 2026-09-28 (web-verified; local probes pending)

Status of everything below: **documented** (verified against PyPI JSON APIs and the GitHub API on
2026-09-28) — nothing is locally executed yet. Local probes are S0 of the round.

- **Exporter:** `litert-torch` 0.9.4 (PyPI, first-party `google-ai-edge`; repo renamed from
  `ai-edge-torch`). Qwen3 is **explicitly supported**: `litert_torch/generative/examples/qwen/`
  contains `qwen3.py` (a `Qwen3(DecoderOnlyModel)` wrapper built from the Edge Generative API
  layers, HF-checkpoint weights loaded via a tensor-name map; example hyperparameters shown are the
  4B: 36 layers, dim 2560 — 0.6B is a config subset), `convert_v3_to_tflite.py`,
  `verify_qwen3.py`. Export exposes `prefill`/`decode` signatures (`prefill_{SEQ-LEN}` naming
  convention). Deps: `torch>=2.4,<2.14` (2.11.0+cpu fits), transformers unpinned (must verify
  against 4.57.6), torchao >=0.17, ai-edge-litert, ai-edge-quantizer 0.9.*, litert-converter 0.4.*,
  jax, jaxtyping. Python >=3.10.
- **Packager:** `litert-lm-builder` 0.17.1 — pure-Python (~38 KB wheel; deps protobuf, flatbuffers,
  absl-py, tomli); "command-line tool and Python API for building and unpacking LiteRT-LM files",
  i.e. the `.litertlm` container (tflite + tokenizer) builder.
- **Runtime:** `litert-lm` 0.17.1 CLI (pure-Python `py3-none-any`; deps litert-lm-api +
  litert-lm-builder pinned 0.17.1, click, prompt_toolkit, questionary; install `uv tool install
  litert-lm`) over `ai-edge-litert` 2.2.0, which ships the **native Linux x86_64 runtime as a
  first-party manylinux wheel** (~91 MB for 2.0.2; macOS arm64 wheels are ~178 KB — the gap is
  bundled native code). LiteRT-LM README lists Qwen among supported model families; the quickstart
  runs Gemma 3n straight from an HF `-litert-lm` repo; v0.16.0 additionally publishes versioned C
  API shared-library prebuilts on GitHub releases.
- **Binary-policy fit:** the ONNX-round precedent applies — declared first-party Google wheels with
  recorded provenance (version + wheel sha256 + loaded-library check); no Bazel/CMake source build
  required. Still owed per plan P5 at execution: audit what `litert-lm` actually loads at runtime
  (no undeclared download-at-first-run), record provenance.
- **Risks:** (1) the qwen3 example re-implements the architecture — adapting the example to
  Qwen3-0.6B is config work, not a one-flag HF export; an alternative "LiteRT Torch Hugging Face
  Export extension" path exists in the docs and must be probed. (2) tokenizer packaging into the
  `.litertlm` bundle (SentencePiece conversion tooling exists: `tokenizer_to_sentencepiece.py`).
  (3) CPU execution-provider evidence for the LiteRT-LM dispatcher on this host is unproven.
- **Scope:** text-generation only (`Qwen/Qwen3-0.6B` @ `c1899de2…`); VLM has "no assumed route"
  per the plan matrix.

## LiteRT-LM round feasibility — resolved 2026-09-28 (execution complete)

The recon section above was confirmed by execution, with these deltas:

- **Exporter:** works, but the reauthored qwen example's default conversion flags produce an
  engine-incompatible graph — `--mask_as_input=True --transpose_kv_cache=True` are mandatory
  (disclosed upstream gap; gemma3/deepseek examples default these True). The `export_hf`
  (one-flag HF) path needs transformers >4.57 (missing `cache_utils.LinearAttentionCacheMixin`)
  and was not used — parity fairness kept transformers at 4.57.6.
- **Exporter dependencies:** tensorflow-cpu is a hard import of the generative path (schema
  codegen); protobuf must be ≥5.26 for litert-lm-builder's gencode.
- **Profile:** fp32 master abandoned — engine graph compilation does not complete in bounded time
  (the exported graph is valid and packs; `describe` works). dynamic_int8 (the converter's
  documented default) ships; context profile 2048 with prefill ladder 8…2048.
- **Packager:** pure-Python, works as documented; TOML `model_type` is written without the
  `tf_lite_` prefix.
- **Runtime:** engine init ≈0.5 s with kernel cache; runtime-download audit clean; the bundled
  `liblitert-lm.so` is the engine. Staged reload byte-identical with cache redirected.
