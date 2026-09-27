# Delivery record — GGUF-first round

Recorded: 2026-09-27, after the P1–P10 sequence of the v2 plan scoped to GGUF.

## Delivery state (explicit, per plan §1 evidence states)

- **Branch pushed**: `feat/hf-generative-model-converter` → `origin` (github.com/rajivmehtaflex/power-utility)
- **MERGED**: PR #2 (https://github.com/rajivmehtaflex/power-utility/pull/2) was marked ready and
  merged on 2026-09-27 (10:56 UTC) as merge commit `c17dbe4f0aa9b89ff5bf3ecfd8ed3d5232c25dc2`;
  `main` now contains the full GGUF round. Feature branch deleted after merge.
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
