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
