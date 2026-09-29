# Validation Report

Generated: 2026-09-17 00:00 UTC

WARN profile/profile/devops/modal-deploy: warning: SKILL.md has 1225 lines (>500 recommended)
WARN profile/profile/mlops/models/audiocraft: warning: SKILL.md has 566 lines (>500 recommended)
WARN profile/profile/mlops/models/segment-anything: warning: SKILL.md has 504 lines (>500 recommended)

Total: 73 skills; 73 spec-compliant; 0 failed

Repo-owned `unsloth-workflows`: spec-compliant; CPU tests pass. Linux/NVIDIA
end-to-end smoke evidence remains pending until a Linux/NVIDIA host is run.

---

## 2026-09-27 addendum — hf-generative-model-converter

Total: 74 skills; 74 spec-compliant; 0 failed (official `skills-ref` validator re-run 2026-09-27;
warnings above predate this addendum and are preserved unchanged).

Repo-owned `hf-generative-model-converter`: spec-compliant; helper tests 29/29 and root
package/catalog tests pass. Real-conversion evidence (GGUF, `Qwen/Qwen3-0.6B` @ `c1899de`, llama.cpp
`v0.5.0`, Linux x86_64 CPU): source build, pinned conversion, functional smoke, staged reload, and a
real private Hub publication with remote content verification (10/10 files hashed) all **passed**;
numerical parity **failed** at the declared Jaccard-0.5 metric on 2/3 short fixtures (the near-limit
fixture matched the reference exactly) and is disclosed on the published model card. Scope: the single
verified recipe plus package/helper/catalog checks; VLM, ONNX, and LiteRT-LM rows remain
pending/unclaimed. Evidence: `docs/superpowers/verification/hf-converter/`.

## 2026-09-28 addendum — hf-generative-model-converter (ONNX round)

Total: 74 skills; 74 spec-compliant; 0 failed (official `skills-ref` validator re-run 2026-09-28).

Repo-owned `hf-generative-model-converter` v0.3.0: spec-compliant; helper tests 30/30 and root
package/catalog tests pass. New verified row: ONNX text-generation (`Qwen/Qwen3-0.6B` @ `c1899de`,
optimum-onnx 0.1.0 / optimum 2.1.0, onnxruntime 1.30.0 declared official wheel with
provenance verified byte-for-byte, Linux x86_64 CPU): locked env, pinned export, functional smoke,
staged reload, and a real private Hub publication with remote content verification (14/14 files
hashed) all **passed**; numerical parity FAILED at the declared Jaccard-0.5 threshold
(0.300/0.171/1.000) and is disclosed on the model card and recipe — not relaxed. VLM ONNX is
deferred (2026-09-28 scope decision); LiteRT-LM remains planned. Recipe evidence:
`assets/recipes.json` (`onnx-qwen3-0.6b-linux-x64-cpu`); run record:
`docs/superpowers/verification/hf-converter/runtime-results-onnx.json`.

## 2026-09-28 addendum — hf-generative-model-converter (LiteRT-LM round)

Total: 74 skills; 74 spec-compliant; 0 failed (official `skills-ref` validator re-run 2026-09-28).

Repo-owned `hf-generative-model-converter` v0.4.0: spec-compliant; helper tests 30/30 and root
package/catalog tests pass. New verified row: LiteRT-LM text-generation (`Qwen/Qwen3-0.6B` @
`c1899de`, litert-torch 0.9.4 + litert-lm-builder 0.17.1 + litert-lm/ai-edge-litert 0.17.1/2.2.0,
all declared official wheels with recorded provenance and a clean runtime-download audit, Linux
x86_64 CPU): locked env, export + `.litertlm` pack, functional smoke, staged reload, and a real
private Hub publication with remote content verification (4/4 files hashed) all **passed**;
numerical parity FAILED at the declared Jaccard-0.5 threshold on 1/3 fixtures (0.300/0.586/0.545,
near-limit fixture passed) and is disclosed — not relaxed. Disclosed upstream gap: the qwen example
requires `--mask_as_input=True --transpose_kv_cache=True` for engine compatibility. All three
targets (GGUF, ONNX, LiteRT-LM) are now conversion-verified for text-generation; VLM rows remain
deferred/not-pursued. Recipe evidence: `assets/recipes.json`
(`litertlm-qwen3-0.6b-linux-x64-cpu`); run record:
`docs/superpowers/verification/hf-converter/runtime-results-litertlm.json`.

## 2026-09-28 addendum — hf-generative-model-converter (quantized GGUF variants)

Total: 74 skills; 74 spec-compliant; 0 failed (official `skills-ref` validator re-run 2026-09-28).

Repo-owned `hf-generative-model-converter` v0.5.0: spec-compliant; helper tests 31/31 (new
`.cache` residue guard) and root package/catalog tests pass. Two new verified rows: GGUF Q8_0
(parity **passed** at the declared Jaccard-0.5 threshold — 0.714/0.833/1.000 — first fully-passing
conversion) and GGUF Q4_K_M (parity **failed**, disclosed) — both functional smoke, staged reload,
and real private publications with remote content verification (10/10 files each). Disclosed:
llama.cpp CPU run-to-run output variance (threading) with the staged-reload gate switched to a
Jaccard criterion; `.cache` residue guard added to the manifest helper after a caught-and-fixed
polluted upload. Recipe evidence: `assets/recipes.json` (`gguf-qwen3-0.6b-q8-0-linux-x64-cpu`,
`gguf-qwen3-0.6b-q4-k-m-linux-x64-cpu`); run record:
`docs/superpowers/verification/hf-converter/runtime-results-quantized.json`.

## 2026-09-29 addendum — hf-generative-model-converter (llama.cpp CUDA accelerator)

Total: 74 skills; 74 spec-compliant; 0 failed (official `skills-ref` validator re-run 2026-09-29).

Repo-owned `hf-generative-model-converter` v0.6.0: spec-compliant; helper tests 31/31 and root package/catalog tests pass. New verified row: llama.cpp CUDA accelerator text-generation (`Qwen/Qwen3-0.6B` @ `c1899de`, llama.cpp `v0.5.0` @ `7fe450e` built with CUDA 12.6 / CUBLAS for sm_75, NVIDIA Tesla T4 GPU 16 GB, Linux x86_64): source build (key `63a9b1871f60ea05`), conversion to F16 GGUF (1.5 GB), functional smoke with full GPU offload to CUDA0 (28/28 layers), staged reload (Jaccard 1.0), and signed artifact manifest all **passed**; numerical parity FAILED at the declared Jaccard-0.5 threshold on 2/3 short fixtures (0.263/0.125/1.000 — near-limit fixture exact match) and is disclosed on the model card and recipe — not relaxed. Hub publication recorded as pending (no HF_TOKEN provided in runtime environment). First verified accelerator route in the catalog. Recipe evidence: `assets/recipes.json` (`gguf-qwen3-0.6b-linux-x64-cuda`); run record: `docs/superpowers/verification/hf-converter/runtime-results-accel-cuda.json`.
