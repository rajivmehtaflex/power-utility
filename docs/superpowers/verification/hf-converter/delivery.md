# Delivery record — GGUF-first round

Recorded: 2026-09-27, after the P1–P10 sequence of the v2 plan scoped to GGUF.

## Delivery state (explicit, per plan §1 evidence states)

- **Branch pushed**: `feat/hf-generative-model-converter` → `origin` (github.com/rajivmehtaflex/power-utility)
- **MERGED**: PR #2 (https://github.com/rajivmehtaflex/power-utility/pull/2) was marked ready and
  merged on 2026-09-27 (10:56 UTC) as merge commit `c17dbe4f0aa9b89ff5bf3ecfd8ed3d5232c25dc2`;
  `main` now contains the full GGUF round. Feature branch deleted after merge.
- **VLM round merged**: PR #3 (https://github.com/rajivmehtaflex/power-utility/pull/3) merged
  2026-09-27 (11:20 UTC) as `8a874447964c5acc963ccf30e6ed21d060a7f375`. `main` now carries two
  conversion-verified tuples: text-generation (Qwen3-0.6B) and vision-language (SmolVLM-256M),
  both GGUF on linux-x86_64 CPU (see runtime-results.json and runtime-results-vlm.json).
- Post-merge verification: CI checks on the PR all passed (`cpu` 12s — green after the B1 dry-run
  fix — and `package` 12s ×2). The pinned `skills` CLI (1.7.0) installed the skill non-interactively
  from the merged `main` (`skills add rajivmehtaflex/power-utility --skill hf-generative-model-converter`)
  into two agent layouts; the installed helper ran from an unrelated cwd and all references,
  both recipes, and the manifest resolved.
- Commits on the branch (oldest first):
  - `5d2a700` docs: carry implementation plan v2
  - `ded085a` build: pinned validator/installer tooling + Unsloth CI validator-route fix
  - `52afb8b` P2 feasibility, compatibility matrix, source-build policy, seeded recipe
  - `d7f0f01` P3 skill core + P4 GGUF recipe with verified source build
  - `05cd30d` P6 manifest/publication helpers + tests
  - `2ce89c5` P7 real conversion acceptance + P8/P9 package/catalog integration
  - `2ce89c5` test: synthetic secret fixture
- **Merge**: performed with the maintainer's authorization (see above).

## Acceptance checks at delivery (plan §6 command set)

All green on the recorded host: pinned skills-ref validation (both owned skills), helper tests
29/29, root package tests 26/26, `MANIFEST.json` valid, `npm ci` from lockfile, `git diff --check`
clean. Secrets/weights scanned over the full branch diff; a real-token-derived test fixture (25-character
prefix of the read token, added in the original `05cd30d`) was replaced with a synthetic token, and
the branch history was subsequently **rewritten and force-pushed** so the fragment no longer exists
in any reachable commit. Because GitHub may serve orphaned pre-rewrite commits by SHA until garbage
collection, **rotation of the read token remains the required complement** and was requested from the
token owner.

## What is claimed vs pending

- **Claimed**: package validated; GGUF recipe documented; llama.cpp source build verified;
  Qwen3-0.6B GGUF conversion verified (functional); publication verified (private test repo,
  10/10 remote files content-verified).
- **Disclosed failure**: numerical fidelity failed at the declared Jaccard-0.5 metric (measured
  0.278/0.097/1.000; near-limit fixture exact) — travels on the model card, EVIDENCE.md, recipes.json.
- **Pending**: VLM tuples, ONNX/LiteRT-LM (P5 parked by scope decision), accelerator backends,
  formal fresh-context behavioral matrix (see behavior-results.json), and merge authorization.

## Access notes

- GitHub: `gh` active account `rajivmehtaflex` (branch push + draft PR used it).
- Hugging Face: write token (user `rajivmehtapy`) used once for the private test-repo publication;
  tokens live only in chmod-600 local files; nothing secret is committed.

## 2026-09-28 — ONNX round merged (PR #4 → `d90ddab`)

Scope: P5 ONNX half, **text-generation only** (VLM ONNX deferred by user scope decision;
LiteRT-LM remains planned). Skill v0.3.0 now advertises `gguf` + `onnx` text-generation on
linux-x86_64 CPU.

- **Verified tuple**: `Qwen/Qwen3-0.6B` @ `c1899de2` → ONNX fp32 (`text-generation-with-past`),
  optimum-onnx 0.1.0/optimum 2.1.0 export, `ORTModelForCausalLM` on onnxruntime 1.30.0.
- **Declared runtime**: official onnxruntime PyPI wheel, provenance verified byte-for-byte
  (wheel `fa688e78…` vs installed native lib `0b2a6e0d…`); `hf-xet` excluded;
  `source-build-verified` NOT claimed for onnx.
- **Results**: functional smoke passed; numerical fidelity failed at the declared Jaccard-0.5
  threshold (0.300/0.171/1.000) — disclosed, not relaxed; staged reload passed byte-identically;
  publication `rajivmehtapy/test-hf-converter-qwen3-0.6b-onnx` @ `92a57de2` (private, 14/14 remote
  files content-verified; receipt at `runs/p9-qwen3-0.6b-onnx/logs/publish_receipt.json`).
- **Disclosed gap**: optimum 2.1.0 qwen3 `head_dim` cache-shape gap → declared
  `embed_size_per_head=head_dim` load patch, documented in recipe/model card/EVIDENCE.
- **Helper**: manifest scanner exemption for the schema-mandated `binary_exceptions[].authorization`
  key (+test); `HF_TOKEN` env-name note for huggingface_hub ≥0.34.
- **CI**: PR #4 checks all green (cpu ×2, package ×2). Full record:
  [runtime-results-onnx.json](runtime-results-onnx.json).

## 2026-09-28 — LiteRT-LM round merged (PR #5 → `92dc663`)

Scope: P5 LiteRT-LM half, **text-generation only** (VLM not pursued — no assumed route per plan
matrix). Skill v0.4.0 now advertises `gguf` + `onnx` + `litert-lm` text-generation on
linux-x86_64 CPU. All three plan targets are conversion-verified.

- **Verified tuple**: `Qwen/Qwen3-0.6B` @ `c1899de2` → `.litertlm` bundle (dynamic-int8, KV 2048),
  litert-torch 0.9.4 + litert-lm-builder 0.17.1; runtime litert-lm 0.17.1 over ai-edge-litert 2.2.0.
- **Declared runtime**: official first-party Google wheels with recorded provenance (incl. bundled
  `liblitert-lm.so` hash) and a clean runtime-download audit; `source-build-verified` NOT claimed.
- **Results**: functional smoke passed; numerical fidelity failed at the declared Jaccard-0.5
  threshold on fixture-1 (0.300/0.586/0.545; near-limit fixture passed) — disclosed, not relaxed;
  staged reload passed byte-identically; publication
  `rajivmehtapy/test-hf-converter-qwen3-0.6b-litertlm` @ `0c725fdd` (private, 4/4 remote files
  content-verified).
- **Disclosed gap**: qwen example default conversion flags → engine-incompatible graph;
  `--mask_as_input=True --transpose_kv_cache=True` mandatory. fp32 profile abandoned (engine
  compilation never completes in bounded time).
- **CI**: PR #5 checks all green (cpu ×2, package ×2). Full record:
  [runtime-results-litertlm.json](runtime-results-litertlm.json).
