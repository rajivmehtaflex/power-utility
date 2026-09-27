# P7 runtime summary — real GGUF conversion acceptance

Full machine-readable record: [runtime-results.json](runtime-results.json).
Claim state after this run, per the plan's evidence-state table:
**GGUF tuple is conversion-verified (functional)** — source build, pinned conversion, bounded target
inference, staged reload, and a real private publication with remote content verification all passed.
**Numerical parity failed at the declared metric** and is disclosed everywhere the claim travels
(model card, EVIDENCE.md, recipes.json, this report). Nothing was relaxed after failure.

## What executed (2026-09-27, host: 4-core Xeon, 11.8 GB avail RAM, no GPU)

1. **Source build** — llama.cpp `v0.5.0` (`7fe450e…`), Release, `LLAMA_CURL=ON`, `-j4`; no
   configure-time downloads; `ldd` shows only build-tree + system libraries; health check
   `0.5.0-dev (build 1, commit 7fe450e)`; binaries hashed into the recipe record.
2. **Acquisition** — `Qwen/Qwen3-0.6B` @ `c1899de…` via resumable snapshot download; 10 files,
   `model.safetensors` 1,503,300,328 bytes; required-file index checked before load.
3. **Conversion** — `convert_hf_to_gguf.py --outtype f16`: 311 tensors → `qwen3-0.6b-f16.gguf`
   (`c8b740a8…e59`), single output as the recipe expects.
4. **Validation** — fixtures frozen before any converted output was inspected (3 synthetic prompts,
   one at ~3900 tokens; greedy, 32 new tokens, raw completion on both sides; metric+threshold
   declared before inspection):
   - Functional smoke: **passed** (nonempty, bound-terminated, no errors, CPU backend only).
   - Numerical fidelity: **failed at Jaccard-0.5** — 0.278 / 0.097 / 1.000. The near-limit fixture
     matched the reference's continuation exactly (31/31 tokens); short fixtures shared the first
     token and then diverged at near-tie greedy decisions. Pattern consistent with cross-implementation
     numeric noise, but the declared rule was not met, so parity is not claimed and the threshold was
     not relaxed. A future recipe revision may declare a prefix-based metric *before* re-running.
5. **Staged reload** — staged package alone under `HF_HUB_OFFLINE=1` from a foreign working directory:
   identical generation. Limitation recorded: OS-level network denial not exercised.
6. **Packaging** — 10-file stage (artifact, processor/config files, LICENSE, model card, sanitized
   evidence); manifest v1 built and verified (exact set, SHA-256, gates, license clear).
7. **Publication** — `hub_publish.py` created a **private** test repo
   `rajivmehtapy/test-hf-converter-qwen3-0.6b-gguf` and published; remote state resolved to commit
   `39da3ef8…`; all 10 files stream-verified by content hash on the remote; receipt kept outside the
   stage with no credentials.

## Corrections made during the run (all recorded in the recipe)

- Pin taken from the annotated tag peel (`7fe450e…`), not the releases API's `target_commitish`.
- `-no-cnv` no longer exists at this pin; `llama-cli` defaults to chat mode and applies the Qwen3
  thinking template — `llama-simple` (greedy, raw completion) is the parity instrument.
- `llama-simple` parses only `-m/-n/-ngl`; prompt must be a single positional argument.
- Converter env: aligned `huggingface-hub<1.0` with transformers 4.57.6; excluded the native `hf-xet`
  extension under the binary policy.

## Remaining pending items (not claimed)

- VLM tuples (SmolVLM support check at this pin) — second pass.
- ONNX and LiteRT-LM targets — plan P5, deferred by the GGUF-first scope decision.
- Accelerator backends — no GPU on this host; unverified.
- Formal fresh-context behavioral matrix (S1–S10) — rubric ready; live development evidence recorded
  in [behavior-results.json](behavior-results.json); formal runs pending.
