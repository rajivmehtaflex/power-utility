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

## ONNX round — 2026-09-28 (P5, ONNX half; VLM deferred by scope decision)

Full record: [runtime-results-onnx.json](runtime-results-onnx.json). Recipe
`onnx-qwen3-0.6b-linux-x64-cpu` rev 1; run `p9-qwen3-0.6b-onnx`.

- **Route:** `Qwen/Qwen3-0.6B` @ `c1899de2…` → ONNX fp32 (`text-generation-with-past`) via
  optimum-onnx 0.1.0 / optimum 2.1.0; inference on onnxruntime 1.30.0 via `ORTModelForCausalLM`.
  No native build: onnxruntime is a **declared official PyPI wheel** — provenance verified
  byte-for-byte (published wheel sha256 `fa688e78…`; installed native lib `0b2a6e0d…` identical);
  `hf-xet` excluded per binary policy. `source-build-verified` is not claimed for this target.
- **Environment:** uv locked env `37261dde718f24a3` (lock `dfbf268e…`), transformers 4.57.6 kept
  from the GGUF env for parity fairness.
- **Fixtures:** frozen before export (same 3 prompts as p7; threshold Jaccard ≥ 0.5 declared up
  front).
- **Results:** functional smoke passed (coherent, factually correct; active provider
  `CPUExecutionProvider`); numerical fidelity **FAILED at the declared threshold**
  (0.300 / 0.171 / 1.000) and is disclosed, not relaxed — near-limit fixture matched the reference
  exactly across 3905-token prefill; short fixtures diverged at greedy near-ties
  (bf16 ref vs fp32 target); staged reload passed byte-identically (offline, cwd `/`).
- **Publication:** private `rajivmehtapy/test-hf-converter-qwen3-0.6b-onnx` @ `92a57de2…`, 14/14
  files stream-verified by content hash; receipt outside the staged inventory.
- **Corrections recorded:** decorator-driven task registration (import the config module before
  probing); optimum qwen3 `head_dim` cache-shape gap → declared `embed_size_per_head` load patch;
  `HF_TOKEN` is the only env name huggingface_hub 0.36 reads; manifest scanner vs
  `binary_exceptions[].authorization` conflict fixed in the helper (narrow exemption + test).

Updated pending list: LiteRT-LM (P5) and quantized GGUF variants remain future rounds; VLM ONNX is
**deferred** (2026-09-28 scope decision), not pending.

## LiteRT-LM round — 2026-09-28 (P5, LiteRT half; VLM not pursued)

Full record: [runtime-results-litertlm.json](runtime-results-litertlm.json). Recipe
`litertlm-qwen3-0.6b-linux-x64-cpu` rev 1; run `p10-qwen3-0.6b-litertlm`.

- **Route:** `Qwen/Qwen3-0.6B` @ `c1899de2…` → `.litertlm` bundle (dynamic-int8, KV 2048) via
  litert-torch 0.9.4 + litert-lm-builder 0.17.1; runtime litert-lm 0.17.1 over ai-edge-litert 2.2.0
  (XNNPACK CPU). No native builds: every native component ships inside a **declared official PyPI
  wheel** (provenance + runtime-download audit recorded); `source-build-verified` is not claimed.
- **Results:** functional smoke passed (3/3 runnable fixtures; engine load ≈0.5 s); numerical
  fidelity **FAILED at the declared threshold on fixture-1** (0.300 / 0.586 / 0.545) and is
  disclosed, not relaxed — fixtures 2 and 4 (near-limit, 1905-token prefill) met the threshold;
  staged reload passed byte-identically (offline, cwd `/`).
- **Publication:** private `rajivmehtapy/test-hf-converter-qwen3-0.6b-litertlm` @ `0c725fdd`, 4/4
  files stream-verified by content hash; receipt outside the staged inventory.
- **Corrections recorded** (all in the recipe + runtime-results): protobuf ≥5.26 needed by
  litert-lm-builder gencode; tensorflow-cpu is a mandatory exporter import; the upstream qwen
  example's default conversion flags produce an **engine-incompatible graph** (prefill fails
  beyond ≈7 tokens) — `--mask_as_input=True --transpose_kv_cache=True` mandatory; fp32 profile
  abandoned (engine graph compilation never completes in bounded time; dynamic_int8 is the
  documented default); profile change 4096→2048 declared with fixture-4 frozen before any target
  run (fixture-3 blocked-by-profile); session-API gotchas (sync decode fails, one session per
  engine, xnnpack cache sidecar).

All three targets (GGUF, ONNX, LiteRT-LM) now carry conversion-verified evidence for
text-generation on linux-x86_64 CPU. Remaining: VLM rows (ONNX deferred, LiteRT not pursued),
quantized GGUF variants, accelerator backends, formal fresh-context behavioral matrix.

## Quantized GGUF variant round — 2026-09-28

Full record: [runtime-results-quantized.json](runtime-results-quantized.json). Run
`p11-qwen3-0.6b-gguf-quantized`; two user-requested variants from the hash-verified F16 master.

- **Q8_0** (805 MB): functional smoke passed; numerical parity **PASSED** at the declared
  Jaccard-0.5 threshold (0.714 / 0.833 / 1.000 — near-limit fixture exact). First conversion in
  the project to fully pass numerical fidelity. Published private @ `5f92cd9c` (10/10 verified).
- **Q4_K_M** (484 MB): functional smoke passed; parity **FAILED** (0.368 / 0.135 / 0.500) —
  disclosed, not relaxed; outputs remain coherent. Published private @ `48b3ec8c` (10/10 verified).
- **Toolchain rebuilt** after the workspace wipe: llama-cli byte-identical to the p7 record;
  llama-quantize hash difference disclosed (VLM-era flag set). Master integrity re-verified from
  its publication before quantization (double-duty as a publication re-check).
- **Protocol change disclosed:** llama.cpp CPU generation is not bit-deterministic across runs
  (threading) — staged-reload gate switched from byte-identity to Jaccard ≥ 0.5 vs validation
  outputs (reload measured 0.889–0.957).
- **Helper hardened:** `hf_hub_download(local_dir=stage)` writes `.cache/huggingface` residue that
  once packaged as junk (first upload deleted + republished clean); `_safe_rel` now rejects `.cache`
  paths and a test covers it (helper tests 31/31).
