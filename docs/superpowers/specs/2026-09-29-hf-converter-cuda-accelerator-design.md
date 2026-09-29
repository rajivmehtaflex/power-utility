# Design Specification: llama.cpp CUDA Accelerator Verification Round

- **Date:** 2026-09-29
- **Author:** Antigravity & User
- **Status:** Approved Draft for Implementation Planning
- **Governing Skill:** `repo-owned/hf-generative-model-converter` (v0.5.0 → v0.6.0)
- **Governing Playbook:** `docs/superpowers/plans/2026-09-28-hf-converter-accelerator-round-playbook.md`

---

## 1. Context & Objective

### 1.1 Context
All prior six verified rounds of `hf-generative-model-converter` were executed on a CPU-only host. Consequently, all six recipe entries in `assets/recipes.json` currently state:
```json
"platform": {
  "build_host": "linux-x86_64",
  "execution": "cpu",
  "accelerator": "none-verified"
}
```

The sole open item remaining across the repository's verification matrix is **verifying accelerator backends**.

### 1.2 Objective
Execute the **llama.cpp CUDA** accelerator round for `Qwen/Qwen3-0.6B` on the detected local NVIDIA Tesla T4 GPU, proving end-to-end compilation, conversion, GPU-offloaded execution, parity evaluation against frozen fixtures, standalone staged reload, SHA-256 manifest generation, conditional Hub publication, and monorepo catalog updates.

---

## 2. Hardware, Environment & Toolchain Prerequisites

### 2.1 Hardware & Driver Environment
- **Host GPU:** NVIDIA Tesla T4 (15,360 MiB / 16 GB VRAM, compute capability 7.5).
- **Driver:** NVIDIA Driver `610.57.04` (active via `/usr/bin/nvidia-smi`).
- **Operating System:** Debian GNU/Linux 11 (Bullseye) x86_64.
- **CPU & Memory:** Linux x86_64 multi-core, >= 12 GB RAM available.

### 2.2 Toolchain Setup
1. **CMake:** Version >= 3.28 required. Managed via `uv tool run --from cmake cmake` or `uv tool install cmake` (providing CMake 4.4.3).
2. **Compiler:** GNU GCC/G++ (10.2.1 / C++17 support).
3. **CUDA Toolkit:** Install the CUDA 12 development toolkit providing `nvcc` and CUDA headers/libraries (`libcudart`, `cublas`, etc.) compatible with driver `610.57.04`.
4. **Environment Verification:** Verify `nvcc --version` and `nvidia-smi` are both functional before attempting builds.

### 2.3 llama.cpp Source Build
- **Source Repository:** `https://github.com/ggml-org/llama.cpp`
- **Pinned Tag / Commit:** Tag `v0.5.0`, commit `7fe450e19305b828c199d602c23a8337aaa1f03b`.
- **Build Key:**
  $$\text{key} = \text{sha256}(\text{commit} \parallel \text{flags} \parallel \text{compiler} \parallel \text{cmake} \parallel \text{dep-lock-sha})[:16]$$
- **Build Directory:** `.hf-converter/builds/<build-key>/`
- **Configuration Flags:**
  ```bash
  cmake <sources>/llama.cpp-v0.5.0 -B .hf-converter/builds/<build-key> \
    -DCMAKE_BUILD_TYPE=Release \
    -DGGML_CUDA=ON \
    -DLLAMA_CURL=ON \
    -DLLAMA_BUILD_TESTS=OFF
  cmake --build .hf-converter/builds/<build-key> --config Release -j 4 \
    --target llama-cli llama-quantize llama-simple
  ```
- **Health Gate:** Check `./bin/llama-cli --version` and audit binary linking with `ldd ./bin/llama-simple | grep -i cuda`. Write the `READY` marker inside the build directory upon success.

---

## 3. Model Acquisition & Target GPU Validation

### 3.1 Model Identity & Integrity
- **Source Model ID:** `Qwen/Qwen3-0.6B`
- **Revision Commit:** `c1899de289a04d12100db370d81485cdf75e47ca` (immutable pin).
- **Integrity Assertion:**
  $$\text{sha256}(\text{model.safetensors}) == \text{f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b}$$

### 3.2 Model Conversion
- **Tool:** `convert_hf_to_gguf.py` from the pinned `llama.cpp` v0.5.0 tree.
- **Command Profile:** `--outtype f16`.
- **Target Artifact:** `.hf-converter/runs/cuda-qwen3-0.6b-f16/work/qwen3-0.6b-f16.gguf`.
- **Quantized Extensions (Optional):** If requested, generate `Q8_0` and `Q4_K_M` variants using the freshly compiled `./bin/llama-quantize` tool from the verified F16 master.

### 3.3 Protocol & Metric Declaration (Prior to Inference)
- **Decoding Configuration:** Pure greedy (`do_sample=False`), seed 42, max 32 new tokens, auto-sized context matching prompt + prediction.
- **Parity Metric:** Token-set Jaccard similarity $\ge 0.50$ per fixture against the CPU PyTorch reference (`reference_outputs.json`).
- **Frozen Fixtures (SHA-256 Verified):**
  1. `fixture-1-short-factual` (`bbaff4d2…`): `"The capital of France is"`
  2. `fixture-2-sentence-task` (`a62337c8…`): `"Write a one-sentence description of the water cycle."`
  3. `fixture-3-near-limit` (`7e5627b1…`): 17,584 character context buffer + tail question.

### 3.4 Target Inference Execution
- **Command:** `./bin/llama-simple -m <gguf> -n 32 "<prompt>" -ngl 99`
- **Hardware Assertion:** Stderr logs **must** confirm active GPU offloading (e.g. `CUDA0` / `ggml_cuda_init` initialized).
- **Output Processing:** Strip prompt echo from stdout to extract raw completion tokens.
- **Parity Assertion & Honesty Rule:** Calculate token-set Jaccard against the PyTorch reference. Any score $< 0.50$ will be formally recorded and disclosed on the model card and recipe limitations; the threshold will never be lowered or hidden.

---

## 4. Staging, Packaging & Manifest Verification

### 4.1 Staged Reload Test
- Populate isolated staging directory (`stage/`) with allowlisted files:
  - `qwen3-0.6b-f16.gguf`
  - `README.md` (model card with license and parity disclosure)
  - `manifest.json`
- **Working Directory Isolation:** Execute target inference with `cwd=/` while source model weights and checkouts are inaccessible.
- **Reload Acceptance Gate:** Fixture completions under reload must achieve token-set Jaccard $\ge 0.50$ against pre-staging GPU validation outputs.

### 4.2 Artifact Manifest Generation
- Execute `scripts/artifact_manifest.py build`:
  - Verify SHA-256 hashes for all staged files.
  - Assert gates `functional_smoke == "passed"` and `staged_reload == "passed"`.
  - Assert license status `clear` (Apache-2.0).
  - Verify zero temporary `.cache` files or extraneous residue.
- Validate manifest structure via `scripts/artifact_manifest.py verify`.

### 4.3 Conditional Hub Publication (Phase 9)
- **Condition A (Token Provided):** If `HF_TOKEN` is found in the local environment, run `scripts/hub_publish.py publish` to upload to private test repository `rajivmehtapy/test-hf-converter-qwen3-0.6b-cuda` with 100% streamed remote content verification.
- **Condition B (Token Missing):** Honestly record Phase 9 as `pending: no HF_TOKEN provided` in the final delivery table without failing the build.

---

## 5. Monorepo Synchronization & Catalog Integrity

### 5.1 Artifacts & Records to Update
1. **`repo-owned/hf-generative-model-converter/assets/recipes.json`:**
   - Add recipe `gguf-qwen3-0.6b-linux-x64-cuda` with:
     ```json
     "platform": {
       "build_host": "linux-x86_64",
       "execution": "cuda",
       "accelerator": "Tesla T4"
     }
     ```
   - Record toolchain build key, compiler, flags, and empirical evidence blocks.
2. **`repo-owned/hf-generative-model-converter/SKILL.md`:**
   - Bump version to `0.6.0`.
   - Update `metadata.verified_targets` to include `gguf: text-generation (Qwen/Qwen3-0.6B) linux-x86_64 CUDA`.
3. **`repo-owned/hf-generative-model-converter/references/compatibility.md`:**
   - Update matrix with the new verified CUDA row and update runtime notes.
4. **`VALIDATION_REPORT.md` & `README.md`:**
   - Append 2026-09-29 addendum documenting the newly verified CUDA accelerator route.
5. **`MANIFEST.json`:**
   - Update skill description and version while preserving strict formatting (`indent=1`, `ensure_ascii=True`).
6. **Verification Logs:**
   - Create `docs/superpowers/verification/hf-converter/runtime-results-accel-cuda.json`.
   - Append summary to `runtime-summary.md` and `delivery.md`.

---

## 6. Regression Testing & Acceptance Gates

Before claiming completion:
1. `uv run --project tools/skill-validation skills-ref validate repo-owned/hf-generative-model-converter` must output `Valid skill`.
2. Skill unit tests must pass:
   ```bash
   uv run --project tools/skill-validation python -m unittest discover -s repo-owned/hf-generative-model-converter/tests
   ```
3. Monorepo package tests must pass:
   ```bash
   uv run --project tools/skill-validation python -m unittest discover -s tests
   ```
4. Git diff audit: Secret scan to verify zero `hf_...` token fragments or hardcoded credentials exist in tracked files.
