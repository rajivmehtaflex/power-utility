# GGUF recipe — llama.cpp, source-built

Verified tuple this recipe documents: `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca`
(decoder-only, text-generation) → GGUF F16, Linux x86_64 **CPU**, llama.cpp `v0.5.0`
(`7fe450e19305b828c199d602c23a8337aaa1f03b`). All values below come from recorded evidence in
`assets/recipes.json` (recipe `gguf-qwen3-0.6b-linux-x64-cpu`). Other models/platforms need their own
recipe row with their own evidence — never reuse this page's pins for a different tuple.

Paths are relative to the run workspace `<user-project>/.hf-converter/` (layout and policy:
[source-builds.md](source-builds.md)). `<key>` is the computed build key
(`198232c63ac3c736` for the recorded run).

## §Build — toolchain from source

1. **Checkout** the pinned revision (tag object `c13fcbf6…` peels to commit `7fe450e…`):

   ```bash
   git clone --branch v0.5.0 https://github.com/ggml-org/llama.cpp sources/llama.cpp-v0.5.0
   git -C sources/llama.cpp-v0.5.0 checkout 7fe450e19305b828c199d602c23a8337aaa1f03b
   ```

2. **Converter env** (Python-only packages, locked): create a uv project whose dependencies are
   llama.cpp's own `requirements/requirements-convert_hf_to_gguf.txt` (torch==2.11.0 from the declared
   CPU index, transformers==4.57.6, numpy~=2.2.6, protobuf>=4.21,<5) plus `huggingface_hub>=0.34,<1.0`,
   and whose `gguf` dependency is the **gguf-py from the same pinned tree** (editable path
   `sources/llama.cpp-v0.5.0/gguf-py`, not PyPI). `uv lock` + `uv sync --locked`. Record the lock's
   sha256 — it feeds the build key.

3. **Native build** (declared system inputs recorded in [source-builds.md](source-builds.md)):

   ```bash
   cmake sources/llama.cpp-v0.5.0 -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=ON -DLLAMA_BUILD_TESTS=OFF
   cmake --build . --config Release -j 4 --target llama-cli llama-quantize
   ```

   Provenance evidence recorded for the verified build: **no configure-time downloads** (ggml and all
   native deps build in-tree); `ldd bin/llama-cli` resolves only build-tree libraries (libllama,
   libggml*, libmtmd, libllama-common) plus system libs — any third `.so` appearing here is a policy
   violation ([source-builds.md](source-builds.md)).

4. **Build key & reuse.** key = sha256(commit ‖ flags ‖ compiler ‖ cmake ‖ dep-lock-sha256)[:16].
   Reuse only if `builds/<key>/READY` exists **and** health passes:

   ```bash
   ./bin/llama-cli --version   # expected: 0.5.0-dev (build 1, commit 7fe450e), GNU 13.3.0, Linux x86_64
   ```

   Recorded binaries (verified build): `llama-cli`
   `91c9a2567adc84a445573e82eea600afc3531cc4a8c357ab162cd216461a4ecd`, `llama-quantize`
   `52fb8ee91d9cda156bad16a7528e3d187f70b1ea7507df9e7c0b2c61ab7b2471`. A build failure keeps logs in
   `builds/<key>/` and **blocks** this tuple — no prebuilt substitution.

## §Acquire — pinned model, verified

Download exactly the pinned revision with the converter env's `huggingface_hub` (resumable, cached):

```bash
uv run --project envs/<key> python -c "
from huggingface_hub import snapshot_download
p = snapshot_download('Qwen/Qwen3-0.6B', revision='c1899de289a04d12100db370d81485cdf75e47ca',
                      local_dir='runs/<run-id>/work/model')
print(p)"
```

Before loading, check the file index against the recipe's `required_files`
(`config.json`, `generation_config.json`, `model.safetensors`, `tokenizer.json`,
`tokenizer_config.json`, `vocab.json`) — a missing or unexpected file stops the run. That list is the
minimal verified acquisition index, not the full repo inventory: the pinned repo also carries
`merges.txt`, `LICENSE`, `README.md` and `.gitattributes`, of which `merges.txt` and `LICENSE` are
carried into the staged package (see `required_files_note` in `assets/recipes.json`). Source access:
public, not gated; license Apache-2.0 (status `clear`, recorded).

## §Convert

```bash
uv run --project envs/<key> python sources/llama.cpp-v0.5.0/convert_hf_to_gguf.py \
  runs/<run-id>/work/model --outfile runs/<run-id>/work/qwen3-0.6b-f16.gguf --outtype f16
```

- Qwen3 conversion support at this pin: `conversion/qwen.py:159` registers `Qwen3ForCausalLM`.
- Tokenizer/template are embedded by the converter from the repo's fast tokenizer files; nothing
  external is merged in.
- Expected output inventory: exactly one `*.gguf` (≈1.2 GB for F16 at 0.6 B params) plus run logs.
  Anything else in `work/` at staging time is unexpected and fails the manifest.
- Optional quantization is a **separate, user-requested step** (`bin/llama-quantize --type <type>`)
  with its own documented acceptance in the recipe record — never a silent default.

## §Run (target inference)

```bash
builds/<key>/bin/llama-simple -m runs/<run-id>/work/qwen3-0.6b-f16.gguf \
  -c 4096 -n 32 --temp 0 --seed 42 -p "<frozen fixture prompt>"
```

`llama-simple` performs raw completion with no chat template — the same semantics as the transformers
raw-reference path, which is what makes the two comparable. **Do not use `llama-cli` for parity runs**
at this pin: it defaults to conversation mode (single turn via `-st`) and applies the Qwen3 thinking
template, so its output distribution differs from a raw reference by design — that was corrected
during P7 after the recorded `-no-cnv` flag turned out to be gone and `-st` runs showed template
insertion (`[Start thinking]`). For an interactive/chat smoke check, `llama-cli -st` is fine, but it
is never the parity instrument.

Record: active backend (CPU expected; a non-CPU backend appearing here is reported, not assumed),
EOS/bound termination, decoded output, and phase timings (observations, not benchmarks). Validation
protocol, fixture rules, and staged-reload requirements: [validation.md](validation.md).

## §VLM note

Multimodal GGUF (e.g. SmolVLM with an mmproj projector) is a **pending support check** at this pin —
this recipe does not cover it; do not run VLM conversions under this recipe. Any future VLM recipe
must add the projector files to its required inventory and the two-image validation protocol.
