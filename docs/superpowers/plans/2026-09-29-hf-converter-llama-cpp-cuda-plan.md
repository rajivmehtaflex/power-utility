# llama.cpp CUDA Accelerator Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile `llama.cpp` with CUDA support on the local NVIDIA Tesla T4 GPU, execute end-to-end GGUF conversion and GPU-offloaded validation for `Qwen/Qwen3-0.6B`, prove standalone staged reload, construct a SHA-256 artifact manifest, conditionally publish to Hugging Face Hub, and update the monorepo catalog and recipes to verify the first accelerator backend.

**Architecture:** A local source build of `llama.cpp` @ `v0.5.0` (`7fe450e1`) is compiled with `-DGGML_CUDA=ON` and assigned a deterministic build key. Conversion transforms pinned `Qwen/Qwen3-0.6B` into an F16 master GGUF. Target inference uses `llama-simple -ngl 99` with GPU offload confirmed in stderr logs (`CUDA0`), followed by token-set Jaccard parity against the frozen CPU reference, standalone reload from `cwd=/`, packaging gate enforcement via `artifact_manifest.py`, and catalog updates across `recipes.json`, `SKILL.md`, `compatibility.md`, and `MANIFEST.json`.

**Tech Stack:** C++17 (`gcc`/`g++` 10.2.1), CMake 4.4.3 (`uv`), CUDA 12 Toolkit (`nvcc`), `llama.cpp` v0.5.0, Python 3.12 (`uv`), `huggingface_hub`, PyTorch.

**Spec:** [`docs/superpowers/specs/2026-09-29-hf-converter-cuda-accelerator-design.md`](file:///root/content/power-utility/docs/superpowers/specs/2026-09-29-hf-converter-cuda-accelerator-design.md)

---

## Global Constraints

- Source model pinned to `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca`.
- Toolchain pinned to `llama.cpp` @ tag `v0.5.0` (`7fe450e19305b828c199d602c23a8337aaa1f03b`).
- No silent prebuilt binaries: native runtime must be built locally from source.
- Strict honesty rule: any sub-0.5 Jaccard score must be disclosed on the model card and recipe; thresholds are never silently lowered.
- Zero secret leakage: `HF_TOKEN` must never be printed, echoed, or committed to git.
- Staging directory must contain zero `.cache` or intermediate conversion residue.
- `MANIFEST.json` formatting must preserve `indent=1` and `ensure_ascii=True`.

---

## Review Focus

1. **CUDA Toolkit & Driver Compatibility:** Driver `610.57.04` is present on the host; compiler must locate `nvcc` and CUDA runtime headers without breaking Debian dependencies.
2. **GPU Execution Assertion:** Stderr logs of `llama-simple` must affirmatively show `CUDA0` and layer offload; CPU fallback must be detected and rejected.
3. **Prompt-Echo Stripping:** `llama-simple` outputs the prompt before generating; verification must accurately strip the exact prompt string before computing Jaccard parity.
4. **Staged Reload Independence:** Model must reload from `stage/` while `cwd=/` and source model directory is inaccessible, proving the GGUF is standalone.
5. **Conditional Hub Publishing:** Missing `HF_TOKEN` must result in a clean `pending` phase status, not a crashed or failed run.

---

### Task 1: Environment & CUDA Development Toolchain Setup

**Files:**
- Modify: `~/.bashrc` (if needed for PATH / LD_LIBRARY_PATH)
- Test: Host terminal checks for `cmake`, `gcc`, `nvcc`, `nvidia-smi`

**Interfaces:**
- Produces: Working `cmake >= 3.28` and `nvcc` compiler on `PATH`.

- [ ] **Step 1: Install modern CMake via `uv`**

Install Kitware CMake via `uv`:
```bash
uv tool install cmake
cmake --version
```
Verify output confirms CMake >= 3.28 (expected `4.4.3`).

- [ ] **Step 2: Install CUDA Developer Toolkit**

Install CUDA toolkit developer packages via `apt-get`:
```bash
apt-get update && apt-get install -y nvidia-cuda-toolkit
```
Ensure `nvcc` is accessible and functional:
```bash
nvcc --version
nvidia-smi
```
Verify `nvcc` prints release information and `nvidia-smi` shows the Tesla T4.

- [ ] **Step 3: Commit environment verification notes**

Document toolchain versions in a temporary environment check script if required.

---

### Task 2: Pinned llama.cpp Source Checkout & CUDA Compilation

**Files:**
- Create: `.hf-converter/sources/llama.cpp-v0.5.0/`
- Create: `.hf-converter/builds/<build-key>/`
- Create: `.hf-converter/builds/<build-key>/READY`

**Interfaces:**
- Consumes: `cmake`, `gcc`, `g++`, `nvcc`.
- Produces: Compiled binaries `./bin/llama-cli`, `./bin/llama-quantize`, `./bin/llama-simple` with CUDA support.

- [ ] **Step 1: Clone and checkout pinned llama.cpp tree**

```bash
mkdir -p .hf-converter/sources
git clone --branch v0.5.0 --single-branch https://github.com/ggml-org/llama.cpp .hf-converter/sources/llama.cpp-v0.5.0
git -C .hf-converter/sources/llama.cpp-v0.5.0 checkout 7fe450e19305b828c199d602c23a8337aaa1f03b
```
Verify commit hash:
```bash
git -C .hf-converter/sources/llama.cpp-v0.5.0 rev-parse HEAD
```
Expected: `7fe450e19305b828c199d602c23a8337aaa1f03b`.

- [ ] **Step 2: Calculate deterministic build key**

Compute build key based on commit, flags (`-DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DLLAMA_CURL=ON -DLLAMA_BUILD_TESTS=OFF`), compiler, and cmake:
```python
import hashlib, subprocess

flags = "-DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DLLAMA_CURL=ON -DLLAMA_BUILD_TESTS=OFF"
commit = "7fe450e19305b828c199d602c23a8337aaa1f03b"
compiler = subprocess.check_output(["gcc", "-dumpversion"]).decode().strip()
cmake_v = subprocess.check_output(["cmake", "--version"]).decode().splitlines()[0]
raw = f"{commit}:{flags}:{compiler}:{cmake_v}"
build_key = hashlib.sha256(raw.encode()).hexdigest()[:16]
print("BUILD_KEY:", build_key)
```

- [ ] **Step 3: Compile with CUDA support**

```bash
mkdir -p .hf-converter/builds/${BUILD_KEY}
cmake -S .hf-converter/sources/llama.cpp-v0.5.0 -B .hf-converter/builds/${BUILD_KEY} \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=ON \
  -DLLAMA_CURL=ON \
  -DLLAMA_BUILD_TESTS=OFF
cmake --build .hf-converter/builds/${BUILD_KEY} --config Release -j 4 \
  --target llama-cli llama-quantize llama-simple
```

- [ ] **Step 4: Verify binary health and CUDA linking**

```bash
./.hf-converter/builds/${BUILD_KEY}/bin/llama-cli --version
ldd ./.hf-converter/builds/${BUILD_KEY}/bin/llama-simple | grep -i cuda
```
Ensure command exits with code 0 and dynamic link list includes CUDA libraries (`libcudart`, `libcublas`).

- [ ] **Step 5: Write READY marker**

```bash
echo "ready" > .hf-converter/builds/${BUILD_KEY}/READY
```

---

### Task 3: Pinned Model Acquisition & GGUF F16 Conversion

**Files:**
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/sources/Qwen3-0.6B/`
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/work/qwen3-0.6b-f16.gguf`

**Interfaces:**
- Consumes: Pinned `convert_hf_to_gguf.py`.
- Produces: Valid `qwen3-0.6b-f16.gguf` artifact with verified SHA-256 hash.

- [ ] **Step 1: Download pinned Qwen/Qwen3-0.6B revision**

Download or symlink snapshot of `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca`:
```bash
python3 -c '
from huggingface_hub import snapshot_download
path = snapshot_download("Qwen/Qwen3-0.6B", revision="c1899de289a04d12100db370d81485cdf75e47ca", local_dir=".hf-converter/runs/cuda-qwen3-0.6b-f16/sources/Qwen3-0.6B")
print("Downloaded to:", path)
'
```

- [ ] **Step 2: Verify model weights SHA-256 integrity**

```bash
sha256sum .hf-converter/runs/cuda-qwen3-0.6b-f16/sources/Qwen3-0.6B/model.safetensors
```
Expected: `f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`.

- [ ] **Step 3: Execute GGUF F16 conversion**

Install conversion python dependencies in a dedicated virtualenv:
```bash
uv venv .hf-converter/envs/gguf-converter --python python3
uv pip --python .hf-converter/envs/gguf-converter install -r .hf-converter/sources/llama.cpp-v0.5.0/requirements.txt
```
Run conversion:
```bash
mkdir -p .hf-converter/runs/cuda-qwen3-0.6b-f16/work
.hf-converter/envs/gguf-converter/bin/python .hf-converter/sources/llama.cpp-v0.5.0/convert_hf_to_gguf.py \
  .hf-converter/runs/cuda-qwen3-0.6b-f16/sources/Qwen3-0.6B \
  --outfile .hf-converter/runs/cuda-qwen3-0.6b-f16/work/qwen3-0.6b-f16.gguf \
  --outtype f16
```
Verify generated file size (~1.2 GB) and record `sha256sum`.

---

### Task 4: Target GPU Validation & Frozen Fixture Parity

**Files:**
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/work/fixtures.json`
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/work/protocol.json`
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/work/target_outputs.json`
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/work/parity_report.json`

**Interfaces:**
- Consumes: `./bin/llama-simple`, `qwen3-0.6b-f16.gguf`.
- Produces: Verified target inference outputs with `CUDA0` confirmation and Jaccard parity measurements.

- [ ] **Step 1: Write frozen fixtures and protocol declaration**

Declare protocol in `protocol.json`:
- Metric: token-set Jaccard similarity >= 0.50
- Sampling: greedy (`do_sample=False`), seed 42, max 32 new tokens
Write fixtures:
- Fixture 1: `"The capital of France is"`
- Fixture 2: `"Write a one-sentence description of the water cycle."`
- Fixture 3: 17,584 character near-limit prompt.

- [ ] **Step 2: Execute GPU inference with offload assertion**

Run each fixture using `llama-simple` with `-ngl 99`:
```bash
./.hf-converter/builds/${BUILD_KEY}/bin/llama-simple \
  -m .hf-converter/runs/cuda-qwen3-0.6b-f16/work/qwen3-0.6b-f16.gguf \
  -n 32 \
  -ngl 99 \
  "<fixture_prompt>" 2> .hf-converter/runs/cuda-qwen3-0.6b-f16/work/infer.log
```
Check `infer.log` for CUDA assertion:
```bash
grep -E "CUDA0|ggml_cuda_init|using CUDA" .hf-converter/runs/cuda-qwen3-0.6b-f16/work/infer.log
```
Assert that offload log exists and generation is non-empty.

- [ ] **Step 3: Strip prompt echo and calculate Jaccard parity**

Compare target completion tokens against the reference outputs in `docs/superpowers/verification/hf-converter/runtime-results.json`:
```python
def jaccard(a: str, b: str) -> float:
  set_a = set(a.strip().split())
  set_b = set(b.strip().split())
  return len(set_a & set_b) / len(set_a | set_b) if (set_a or set_b) else 1.0
```
Save calculated scores to `parity_report.json`.

---

### Task 5: Staged Reload, Manifest Packaging & Conditional Publication

**Files:**
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/stage/`
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/stage/manifest.json`
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/stage/README.md`
- Create: `.hf-converter/runs/cuda-qwen3-0.6b-f16/logs/publish_receipt.json` (conditional)

**Interfaces:**
- Consumes: `artifact_manifest.py`, `hub_publish.py`.
- Produces: Confirmed standalone reload and valid signed manifest.

- [ ] **Step 1: Populate stage directory**

```bash
mkdir -p .hf-converter/runs/cuda-qwen3-0.6b-f16/stage
cp .hf-converter/runs/cuda-qwen3-0.6b-f16/work/qwen3-0.6b-f16.gguf .hf-converter/runs/cuda-qwen3-0.6b-f16/stage/
```
Generate model card `README.md` with:
- Model metadata and Apache-2.0 license tags
- Verification host information: Linux x86_64, NVIDIA Tesla T4
- Parity measurements and disclosures

- [ ] **Step 2: Execute staged reload test from root working directory**

Run `llama-simple` from `cwd=/` pointing to `.hf-converter/runs/cuda-qwen3-0.6b-f16/stage/qwen3-0.6b-f16.gguf` while the source weights directory is renamed or inaccessible. Verify output matches previous run with Jaccard >= 0.50.

- [ ] **Step 3: Build and verify artifact manifest**

```bash
python3 repo-owned/hf-generative-model-converter/scripts/artifact_manifest.py build \
  --stage .hf-converter/runs/cuda-qwen3-0.6b-f16/stage \
  --manifest .hf-converter/runs/cuda-qwen3-0.6b-f16/stage/manifest.json \
  --model-id "Qwen/Qwen3-0.6B" \
  --revision "c1899de289a04d12100db370d81485cdf75e47ca" \
  --recipe "gguf-qwen3-0.6b-linux-x64-cuda"
```
Verify manifest structure:
```bash
python3 repo-owned/hf-generative-model-converter/scripts/artifact_manifest.py verify \
  --stage .hf-converter/runs/cuda-qwen3-0.6b-f16/stage \
  --manifest .hf-converter/runs/cuda-qwen3-0.6b-f16/stage/manifest.json
```
Assert that verification passes cleanly.

- [ ] **Step 4: Execute conditional Hub publication**

```bash
if [ -n "$HF_TOKEN" ]; then
  python3 repo-owned/hf-generative-model-converter/scripts/hub_publish.py publish \
    --stage .hf-converter/runs/cuda-qwen3-0.6b-f16/stage \
    --manifest .hf-converter/runs/cuda-qwen3-0.6b-f16/stage/manifest.json \
    --repo-id "rajivmehtapy/test-hf-converter-qwen3-0.6b-cuda" \
    --visibility private \
    --create
else
  echo "HF_TOKEN not set; skipping Hub publication (recorded as pending)."
fi
```

---

### Task 6: Monorepo Catalog, Recipe & Verification Updates

**Files:**
- Modify: `repo-owned/hf-generative-model-converter/assets/recipes.json`
- Modify: `repo-owned/hf-generative-model-converter/SKILL.md`
- Modify: `repo-owned/hf-generative-model-converter/references/compatibility.md`
- Modify: `VALIDATION_REPORT.md`
- Modify: `README.md`
- Modify: `MANIFEST.json`
- Create: `docs/superpowers/verification/hf-converter/runtime-results-accel-cuda.json`
- Modify: `docs/superpowers/verification/hf-converter/runtime-summary.md`
- Modify: `docs/superpowers/verification/hf-converter/delivery.md`

**Interfaces:**
- Produces: Spec-compliant skill package with updated recipes, documentation, and regression tests passing.

- [ ] **Step 1: Add new CUDA recipe to `assets/recipes.json`**

Insert `gguf-qwen3-0.6b-linux-x64-cuda` entry containing:
- `platform`: `build_host: "linux-x86_64"`, `execution: "cuda"`, `accelerator: "Tesla T4"`
- Recorded `build_key`, compilation flags, binary hashes, and passed evidence.

- [ ] **Step 2: Update `SKILL.md` and `references/compatibility.md`**

Bump `SKILL.md` version to `0.6.0`, add CUDA text-generation to `metadata.verified_targets`. Add verified CUDA row to `references/compatibility.md`.

- [ ] **Step 3: Update `VALIDATION_REPORT.md` and `README.md`**

Add addendum to `VALIDATION_REPORT.md` and update `README.md` verified routes table.

- [ ] **Step 4: Sync `MANIFEST.json`**

Update skill entry description in `MANIFEST.json` preserving formatting (`indent=1`, `ensure_ascii=True`).

- [ ] **Step 5: Write verification records**

Write `runtime-results-accel-cuda.json` and append section to `runtime-summary.md` and `delivery.md`.

- [ ] **Step 6: Run full test regression suite**

```bash
uv run --project tools/skill-validation skills-ref validate repo-owned/hf-generative-model-converter
uv run --project tools/skill-validation python -m unittest discover -s repo-owned/hf-generative-model-converter/tests
uv run --project tools/skill-validation python -m unittest discover -s tests
```
Ensure all tests exit code 0.

- [ ] **Step 7: Audit git diff and commit**

```bash
git diff --check
git status
```
Verify zero secrets or unintended cache files are tracked. Commit all changes.
