# Playbook — hf-generative-model-converter: accelerator-backends round (the pending task)

Authored 2026-09-28 on the development host. Purpose: hand this file to a **fresh clone of
`rajivmehtaflex/power-utility` on a different machine** (with accelerator hardware) so an agent with
no prior context can execute the one remaining open round of the project, following the exact
discipline the six verified rounds used.

Read order for the fresh agent: this file → `docs/superpowers/verification/hf-converter/delivery.md`
(project history) → `repo-owned/hf-generative-model-converter/SKILL.md` (the skill itself) → the
recipe you are extending in `repo-owned/hf-generative-model-converter/assets/recipes.json`.

---

## 1. Project state snapshot (as of 2026-09-28, main @ `70e4cad`)

The skill `hf-generative-model-converter` (v0.5.0, repo-owned) converts pinned HF generative models
to **GGUF**, **ONNX**, and **LiteRT-LM (`.litertlm`)**, validates by real inference against frozen
fixtures, and publishes verified packages to the Hub behind a SHA-256 manifest and a guarded
publication helper. **All three plan targets are conversion-verified for text-generation on
linux-x86_64 CPU** (skill v0.5.0):

| Verified route | Recipe id | Publication (private) |
|---|---|---|
| GGUF F16 master | `gguf-qwen3-0.6b-linux-x64-cpu` | `rajivmehtapy/test-hf-converter-qwen3-0.6b-gguf` @ `39da3ef8` |
| GGUF Q8_0 (parity **passed** 0.714/0.833/1.000) | `gguf-qwen3-0.6b-q8-0-linux-x64-cpu` | `rajivmehtapy/test-hf-converter-qwen3-0.6b-gguf-q8-0` @ `5f92cd9c` |
| GGUF Q4_K_M (parity failed, disclosed) | `gguf-qwen3-0.6b-q4-k-m-linux-x64-cpu` | `rajivmehtapy/test-hf-converter-qwen3-0.6b-gguf-q4-k-m` @ `48b3ec8c` |
| GGUF VLM two-image protocol | `gguf-smolvlm-256m-linux-x64-cpu` | `rajivmehtapy/test-hf-converter-smolvlm-256m-gguf` @ `5aedf072` |
| ONNX fp32 text-gen | `onnx-qwen3-0.6b-linux-x64-cpu` | `rajivmehtapy/test-hf-converter-qwen3-0.6b-onnx` @ `92a57de2` |
| LiteRT-LM int8 text-gen | `litertlm-qwen3-0.6b-linux-x64-cpu` | `rajivmehtapy/test-hf-converter-qwen3-0.6b-litertlm` @ `0c725fdd` |

Behavioral audit: **complete** — all 10 scenarios carry formal fresh-context runs (guided 10/10;
S2/S5 at the 5×5 sample budget); see `docs/superpowers/verification/hf-converter/behavior-results.json`.

## 2. The pending task

**Verify accelerator backends.** Every recipe row today says `execution: cpu,
accelerator: none-verified` because the development host had no GPU. The task: pick at least one
backend from §5, re-run the full round chain on it, and record it as verified. Requirements were
sized in `README.md` § "Verification hardware requirements":

| Backend | Hardware | Software | New recipe platform values |
|---|---|---|---|
| **llama.cpp CUDA** (recommended first — covers the most) | Any CUDA-capable NVIDIA GPU, compute capability ≥ 6.1, ≥ 6 GB VRAM (F16 0.6B needs ~2–3 GB) | NVIDIA driver ≥ 535, CUDA toolkit 12.x (`nvcc` on PATH), ~10 GB disk | `execution: cuda`, `accelerator: <gpu-name>`, host unchanged |
| **onnxruntime GPU** | Same NVIDIA GPU | Driver ≥ 535 + CUDA 12.x + cuDNN 9.x matching the `onnxruntime-gpu` wheel | `execution: cuda`, `accelerator: <gpu-name>` |
| **llama.cpp Metal** | Apple Silicon M1+, ≥ 8 GB unified memory | macOS + Xcode CLT | `build_host: macosx-arm64`, `execution: metal` |
| **llama.cpp Vulkan** | Any Vulkan 1.2+ GPU (AMD/Intel included) | Vulkan loader + SDK (`glslc`) | `execution: vulkan` |
| **LiteRT GPU** | GPU with OpenCL/OpenGL or WebGPU support | ai-edge-litert 2.2.0 bundles GPU/WebGPU accelerators | `execution: gpu` |

Parked/blocked (do **not** spend time unless conditions change):
- **VLM ONNX — blocked**: `idefics3` is not registered in optimum-onnx 0.1.0's export mapping (the
  latest release). Re-open only if a newer optimum-onnx registers it (re-probe with the one-liner in
  `docs/superpowers/verification/hf-converter/runtime-results-vlm-onnx-probe.json`).
- **VLM LiteRT — not pursued** (no assumed route in the plan matrix).
- **Larger model scales** (e.g., 7B) — a new scope row, not part of this round.

## 3. Machine prerequisites (before anything)

1. Clone: `git clone https://github.com/rajivmehtaflex/power-utility && cd power-utility`.
2. Toolchain: `uv` (≥ 0.11), `git`, `python3.12`, `cmake ≥ 3.28`, C++17 compiler; GPU stack per §2.
3. GitHub auth: `gh auth login` as **`rajivmehtaflex`** (verify with `gh auth status`). If pushes
   fail with `could not read Password for 'https://rajivmehtapy@github.com'`, a stale
   `credential.https://github.com.username` is set — remove it:
   `git config --global --unset credential.https://github.com.username` (this has recurred after
   workspace restarts).
4. HF auth: tokens (read + write role for user **`rajivmehtapy`**) live in
   `~/.config/hf-converter/hf.env` (chmod 600). **Gotcha:** they must be written `export VAR=value`
   — spaces around `=` silently produce empty variables in zsh. Source it and map
   `HF_TOKEN="$HUGGINGFACEHUB_API_TOKEN_WRITE"` for publish commands (huggingface_hub ≥ 0.34 reads
   **`HF_TOKEN`** only; the legacy `HUGGINGFACEHUB_API_TOKEN` name is ignored). Never print, echo,
   commit, or store token values anywhere. Validate: `whoami-v2` returns 200 for both tokens.
5. Sanity: `uv run --project tools/skill-validation skills-ref validate
   repo-owned/hf-generative-model-converter` must print "Valid skill" on the fresh clone.

## 4. The round protocol (identical for every backend — do not skip steps)

Run as a **feature branch + PR** (`feat/hf-converter-accel-<backend>`); merge on green CI.

1. **Freeze first.** Reconstruct the three frozen fixture prompts and verify their SHA-256 against
   `docs/` records — the exact prompts and hashes are in
   `.hf-converter/runs/p7-qwen3-0.6b-f16/work/fixtures.json` (also mirrored in this repo's
   `docs/superpowers/verification/hf-converter/runtime-results.json`):
   - fixture-1-short-factual `bbaff4d2…` = "The capital of France is"
   - fixture-2-sentence-task `a62337c8…` = "Write a one-sentence description of the water cycle."
   - fixture-3-near-limit `7e5627b1…` = filler repeated to 17584 chars + tail (reconstruct
     deterministically: `"The quick brown fox jumps over the lazy dog. "` ×N + `"In summary,
     according to the repeated sentence above, what animal is mentioned?"`, length < 17584, and
     verify the hash).
   **Declare the metric and threshold in writing before producing any target output**: token-set
   Jaccard ≥ 0.5 per fixture, greedy, seed 42, 32 new tokens, raw completion. This declaration is
   non-negotiable and must precede conversion (record it in a `protocol.json` under the run).
2. **Reference.** Reuse the recorded reference outputs (same model revision, same protocol) from
   `.hf-converter/runs/p7-qwen3-0.6b-f16/work/reference_outputs.json` — do not re-run the torch
   reference unless the model revision changed. If that file is absent on the new machine, copy it
   out of this repository's history or regenerate it once on CPU before touching the GPU (it is the
   *source-model* reference, independent of deployment backend).
3. **Source or declared runtime.** llama.cpp: build from the pinned tree (see §5) — a **new build
   key** because flags change: key = sha256(commit ‖ flags ‖ compiler ‖ cmake ‖ dep-lock-sha)[:16],
   directory `builds/<key>/`, `READY` marker only after a health check (`llama-cli --version`).
   onnxruntime: the GPU wheel is a **declared binary** (policy: no *silent* prebuilt) — record wheel
   name + sha256 from the locked `uv.lock` + confirm the loaded native lib matches, and add it to
   `toolchain.declared_binary_exceptions[].authorization` in the manifest metadata.
4. **Convert** the pinned revision `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca`.
   Verify `sha256(model.safetensors) == f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`
   (== HF LFS oid at the pin) before loading. The F16 GGUF may also be recovered from its verified
   publication and re-hashed (`c8b740a8…`) — never skip that check.
5. **Validate.** Functional smoke: nonempty coherent output per fixture, clean bound termination,
   assert the GPU backend is actually active (llama.cpp prints `CUDA0`/`Metal` in the log; ORT:
   `session.get_providers()`; LiteRT: engine accelerator registry). Parity: token-set Jaccard at the
   declared threshold, **failure is disclosed, never relaxed** (a failed variant shipped with full
   disclosure in round p11 — that is the correct precedent).
6. **Staged reload.** Copy the package to `stage/`, run from `cwd=/` with the source model absent,
   regenerate all fixtures, and compare with the Jaccard gate (≥ 0.5 vs validation-run outputs).
   **Byte-identity is unattainable** — llama.cpp CPU/GPU generation is not bit-deterministic across
   runs (threaded reductions flip near-tie tokens; observed 0.889–0.957 Jaccard on CPU in round
   p11). Never hf_hub_download into the stage dir (residue guard exists, but keep the stage clean).
7. **Manifest.** `scripts/artifact_manifest.py build/verify` on the stage (gates enforced:
   functional_smoke + staged_reload must be `passed`, license `clear`, model-card present).
8. **Publish** with `scripts/hub_publish.py publish --stage … --manifest …
   --repo-id rajivmehtapy/test-hf-converter-qwen3-0.6b-<backend> --visibility private --create`.
   The helper refuses publication unless every gate passes, then stream-verifies every remote file.
   Save the printed receipt to the run's `logs/` (it contains no credentials).
9. **Record.** New `recipes.json` row(s) (`gguf-qwen3-0.6b-<backend>-linux-x64-cuda` etc., evidence
   states per the table in the plan), `SKILL.md` version bump + `verified_targets` update,
   `references/compatibility.md` rows (replace "CPU-only" limitation lines for verified backends),
   `VALIDATION_REPORT.md` addendum, `README.md` verified-routes row,
   `docs/superpowers/verification/hf-converter/runtime-results-accel-<backend>.json`,
   `runtime-summary.md` + `delivery.md` appends, `MANIFEST.json` description sync (keep `indent=1`,
   `ensure_ascii=True` — a naive rewrite churns the whole catalog).
10. **Validators before pushing**: skills-ref valid; skill helper tests
    (`uv run --project tools/skill-validation python -m unittest discover -s
    repo-owned/hf-generative-model-converter/tests` — currently 31); package tests
    (`… discover -s tests` — currently 19); secret-scan the diff for `hf_[A-Za-z0-9]{16,}`.

## 5. Backend-specific runbooks

### 5a. llama.cpp CUDA (start here)

```bash
git clone --branch v0.5.0 --single-branch https://github.com/ggml-org/llama.cpp \
  .hf-converter/sources/llama.cpp-v0.5.0
git -C .hf-converter/sources/llama.cpp-v0.5.0 checkout 7fe450e19305b828c199d602c23a8337aaa1f03b
cmake .hf-converter/sources/llama.cpp-v0.5.0 -B .hf-converter/builds/<new-key> \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DLLAMA_CURL=ON -DLLAMA_BUILD_TESTS=OFF
cmake --build .hf-converter/builds/<new-key> --config Release -j <cores> \
  --target llama-cli llama-quantize llama-simple
```

- Record: `nvcc --version`, driver (`nvidia-smi`), GPU name/VRAM, the new build key, binary hashes,
  `ldd`/DLL audit (CUDA libs expected now — declare them in the recipe, they are *expected*
  toolchain components, not prebuilt substitutions).
- Inference: `llama-simple -m <gguf> -n 32 <prompt>` with `-ngl 99` (or llama-simple's equivalent —
  it parses only `-m/-n/-ngl`); confirm `CUDA0` in the log. Same frozen fixtures, same stripping of
  the prompt echo from stdout.
- Quantized variants (optional extension): re-run `llama-quantize` Q8_0/Q4_K_M and validate on GPU
  too — the Q8_0 CPU row passed parity, so the GPU row should be compared against the same metric.

### 5b. onnxruntime GPU

- Locked env: restore from the ONNX round (`envs/37261dde718f24a3/pyproject.toml` + `uv.lock` are
  committed evidence; swap `onnxruntime==1.30.0` for `onnxruntime-gpu` of the matching major, re-lock,
  **new env key** = sha256(commit ‖ pyproject ‖ lock)[:16] computed **before** `uv sync`, final
  directory created first — a post-sync rename breaks console-script shebangs).
- The ONNX export itself is backend-independent: reuse the verified CPU export
  (`model.onnx` + `model.onnx_data` from the published ONNX repo, re-hash `76a3ec83…` /
  `aa3afc2df…`) or re-export with the recorded command in `references/onnx.md`.
- Load: `ORTModelForCausalLM.from_pretrained(..., provider=["CUDAExecutionProvider"])`; assert the
  active provider; **keep the declared qwen3 patch** (`model.embed_size_per_head =
  model.config.head_dim` — optimum ignores qwen3's explicit head_dim; without it decode fails
  `Got: 64 Expected: 128`).
- Parity vs the same reference; disclose any provider-specific numeric differences.

### 5c. llama.cpp Metal (macOS arm64)

- Same pinned checkout; Metal is enabled by default on macOS (`-DGGML_METAL=ON`); record
  `system_profiler SPHardwareDataType`, chip, unified memory, `xcodebuild -version`.
- `-ngl 99`; Metal kernel cache lands beside the binary/model — keep it out of stages.
- New `build_host: macosx-arm64` — this closes the macOS-host gap recorded in every recipe's
  limitations. All records/validators are host-agnostic (pure Python + JSON).

### 5d. llama.cpp Vulkan

- `-DGGML_VULKAN=ON` with the Vulkan SDK installed (`glslc` required by the build); record
  `vulkaninfo` GPU/driver summary. Same validation chain; watch for first-run shader compile time.

### 5e. LiteRT GPU

- The engine already registers GPU/WebGPU accelerators (visible in every run log); probe
  `litert-lm run <bundle> --backend=gpu …` on the target machine. If the WebGPU path needs extra
  system packages, record them as build_host notes. If the GPU delegate refuses the int8 bundle,
  that outcome is recorded honestly as `blocked: <named obstacle>` for the GPU row — the CPU row
  stays verified.

## 6. Non-negotiable rules (violating any of these invalidates the round)

1. **Immutable pins**: model revision, toolchain commit, dependency locks — never "latest".
2. **No silent prebuilt binaries**: local builds for llama.cpp; otherwise *declared* official wheels
   with recorded provenance (wheel sha256 + loaded-library check) and `authorization` text.
3. **Fixtures and thresholds are declared before any converted output exists.** Never relax a
   threshold after a failure — a failure is disclosed (see Q4_K_M, ONNX, LiteRT-LM rows).
4. **Validation before publication**: functional smoke + staged reload gates are enforced by the
   manifest helper; it refuses otherwise. Never bypass it.
5. **Credentials**: only from local Hub config; never echo/store/commit; `HF_TOKEN` env name;
   publications only to `rajivmehtapy/…` private test repos unless the user explicitly says otherwise.
6. **Claims never exceed evidence**: `source-build-verified` only where a build actually happened;
   disclose every deviation, hash difference, and nondeterminism observation.
7. **CPU run-to-run nondeterminism is a recorded fact** (round p11) — use the Jaccard reload gate,
   not byte-identity, everywhere.

## 7. Gotchas that have already cost time (learned the hard way)

- `export VAR = value` (spaces around `=`) silently yields empty vars in zsh.
- Stale `credential.https://github.com.username=rajivmehtapy` reappears after workspace restarts →
  push failures; unset it (§3.3).
- huggingface_hub ≥ 0.34 reads `HF_TOKEN` only — `HUGGINGFACEHUB_API_TOKEN` is dead.
- `hf_hub_download(local_dir=<stage>)` writes `.cache/huggingface` residue into the package; the
  helper now rejects `.cache` paths (build fails loudly). Download to a scratch dir and copy.
- protobuf: litert-lm-builder's gencode needs `protobuf>=5.26`; llama.cpp's converter needs `<5`.
  Different envs, different pins — do not merge them.
- litert-torch's generative exporter hard-imports `tensorflow.lite.python.schema_py_generated` →
  tensorflow-cpu is a mandatory dependency of that env.
- optimum task mapping reads empty until `import optimum.exporters.onnx.model_configs` (decorator
  registration).
- optimum 2.1.0 qwen3 gap: `embed_size_per_head = config.head_dim` patch required at ORT inference.
- venv directories must not be renamed after `uv sync` (shebangs embed absolute paths).
- Env build keys are computed from `sha256(commit ‖ pyproject ‖ lock)[:16]` BEFORE `uv sync`.
- llama.cpp CUDA/Metal/Vulkan builds change the binary hashes vs the CPU record — expected; record
  the new hashes and the flag diff, and say why.

## 8. Definition of done (per backend)

- [ ] New recipe row with `source_build` or declared-wheel environment evidence `passed`, build key,
      binary/wheel hashes, and platform values reflecting the actual backend
- [ ] Functional smoke on the GPU backend with the active-backend assertion recorded
- [ ] Parity measured at the declared threshold — passed, or failed **and disclosed**
- [ ] Staged reload passed under the Jaccard gate
- [ ] Private publication with 10/10 (or N/N) streamed remote verification + receipt in run logs
- [ ] `SKILL.md` bumped; `verified_targets`/README/compatibility/catalog/VALIDATION_REPORT updated
- [ ] `runtime-results-accel-<backend>.json` written; `runtime-summary.md` + `delivery.md` appended
- [ ] skills-ref valid; helper tests green; package tests green; PR merged to `main`; CI green

Suggested first milestone: **llama.cpp CUDA on one GPU machine** — it reuses the most existing
machinery (same build tree, same fixtures, same helper) and unlocks both the CUDA row and (with
`llama-quantize`) GPU quantized-variant rows in one round.
