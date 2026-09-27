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
