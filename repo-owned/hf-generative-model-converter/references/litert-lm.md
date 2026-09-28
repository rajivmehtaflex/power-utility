# LiteRT-LM recipe — litert_torch export + .litertlm bundle (declared official wheels)

Verified tuple this recipe documents: `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca`
(decoder-only, text-generation) → `.litertlm` bundle (dynamic-int8 weights, fp32 KV cache, context
2048), Linux x86_64 **CPU**, litert-torch `0.9.4`, litert-lm-builder `0.17.1`, litert-lm `0.17.1` +
ai-edge-litert `2.2.0`, tensorflow-cpu `2.21.0`, transformers `4.57.6`, torch `2.11.0+cpu`. All
values below come from recorded evidence in `assets/recipes.json` (recipe
`litertlm-qwen3-0.6b-linux-x64-cpu`). Other models/platforms need their own recipe row with their
own evidence — never reuse this page's pins for a different tuple.

**Scope:** text-generation only. VLM has no assumed route in LiteRT (plan matrix) — do not attempt
it under this recipe.

## §Toolchain — locked env, declared wheels (no native build)

No component is built from source. Every native piece ships inside a **declared official PyPI
wheel** (first-party Google distributions); the source policy forbids *silent* prebuilt binaries —
these declarations carry recorded provenance (wheel sha256 from the locked `uv.lock`, plus the
bundled-engine hash). `source-build-verified` is **not** claimed for this target.

Recorded provenance (env key `3fdb8eb251c31330`, lock sha256
`b98e8bb42e764df39af115bb95c1842dce2cec511ba2b1514f0fc9cfea01ca48`, 82 packages):

| Component | Wheel | sha256 |
|---|---|---|
| litert-torch (exporter) | `litert_torch-0.9.4-py3-none-any.whl` | `e338b9dd…d91b6353` |
| litert-lm (CLI + bundled native engine) | `litert_lm-0.17.1-py3-none-any.whl` | `ef9372fa…5a28333f` |
| litert-lm-builder (packer) | `litert_lm_builder-0.17.1-py3-none-any.whl` | `fdfe7d15…e196ce4c` |
| ai-edge-litert (runtime) | `ai_edge_litert-2.2.0-cp312-cp312-manylinux_2_27_x86_64.whl` | `4e151f07…6b81f50a` |
| tensorflow-cpu (exporter dep) | `tensorflow_cpu-2.21.0-cp312-cp312-manylinux_2_27_x86_64.whl` | `dcc8afd3…f0f820cb` |

The "pure-Python" `litert_lm` wheel bundles the native engine `liblitert-lm.so`
(`f202ca2351db108105fed241cd731266255c2471f3ed850c265d0c29d27fd841` at this pin). Runtime-download
audit: no network-download code paths exist in `litert_lm`, `litert_lm_api` or `litert_lm_builder`
(source-audited 2026-09-28); the only Hub client is the user-invoked `import
--from-huggingface-repo` helper, which this recipe never uses. `hf-xet` is excluded via
`override-dependencies` per the binary policy.

**Environment** (uv project; `torch==2.11.0` from the declared `pytorch-cpu` index, same as the
GGUF/ONNX envs for parity fairness): torch, transformers, huggingface_hub, sentencepiece,
protobuf (⚠ `>=5.26,<8` — litert-lm-builder's gencode needs `protobuf.runtime_version`; the
`<5` pin carried from the GGUF env breaks the CLI at import), litert-torch, ai-edge-litert,
litert-lm, litert-lm-builder, tensorflow-cpu (`litert_torch.generative.layers.lora` hard-imports
`tensorflow.lite.python.schema_py_generated`). Compute the env build key
`sha256(commit ‖ pyproject ‖ lock)[:16]` **before** `uv sync` and create the final directory first:
a post-sync rename breaks console-script shebangs (absolute interpreter paths).

## §Acquire — pinned model, verified

Snapshot the pinned revision; verify `sha256(model.safetensors)` equals the HF LFS oid at the pin
(`f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`, via
`/api/models/Qwen/Qwen3-0.6B/tree/<revision>`) before loading. License Apache-2.0, public, not
gated.

## §Convert — freeze fixtures FIRST

Freeze fixtures and thresholds before running any conversion (see [validation.md](validation.md));
the recorded run froze 3 prompts + token-set Jaccard ≥ 0.5, and added a 1905-token near-limit
fixture when the profile changed, before any target run.

```bash
python -m litert_torch.generative.examples.qwen.convert_v3_to_tflite \
  --model_size=0.6b \
  --checkpoint_path=runs/<run-id>/work/model \
  --output_path=runs/<run-id>/work \
  --output_name_prefix=qwen3-0.6b-int8-ekv2048 \
  --quantize=dynamic_int8 \
  --mask_as_input=True --transpose_kv_cache=True \
  --kv_cache_max_len=2048 \
  --prefill_seq_lens=8 --prefill_seq_lens=64 --prefill_seq_lens=128 --prefill_seq_lens=256 \
  --prefill_seq_lens=512 --prefill_seq_lens=1024 --prefill_seq_lens=2048 \
  --decode_batch_size=1
```

- **The two boolean flags are mandatory** (disclosed upstream gap): with the example's default
  flags (`mask_as_input=False`, `transpose_kv_cache=False`) the exported graph is accepted by the
  packer but the litert-lm engine fails prefill for any input longer than ≈7 tokens
  (`FAILED_PRECONDITION: Prefill input length exceeds available state entries (remaining
  capacity: 8)`). gemma3/deepseek examples default these flags to `True`; the qwen example does
  not. Verified empirically: with the flags, prefills of 8…1905 tokens all succeed.
- `--quantize=dynamic_int8` is the converter's documented default and the recorded profile. An
  fp32 (`--quantize=none`) export was also produced and documented: it packs and `describe` works,
  but engine graph compilation does not complete in bounded time (>40 min at 200% CPU on the
  recorded 4-core host) — do not ship it; treat fp32 as a research profile needing its own
  acceptance.
- The converter emits one multi-signature `.tflite` (`prefill_8…prefill_2048` + `decode`);
  `TF_ENABLE_ONEDNN_OPTS=0` was set during conversion (recorded setting).
- `--kv_cache_max_len` bounds total context (prefill + generated tokens). fixture prompts must fit
  inside it — a prompt longer than the profile fails prefill by design (recorded as
  blocked-by-profile, not a conversion failure).

## §Pack — .litertlm bundle

Bundle sections (TOML understood by `litert-lm pack`; note `model_type` is written **without** the
`tf_lite_` prefix — the builder adds it):

```toml
[[section]]
section_type = "TFLiteModel"
data_path = "model.tflite"
model_type = "prefill_decode"

[[section]]
section_type = "HF_Tokenizer"
data_path = "tokenizer.json"

[[section]]
section_type = "LlmMetadata"
data_path = "llm_metadata.text_proto"
```

`llm_metadata.text_proto` (Qwen3-0.6B): `start_token { token_str: "<|im_start|>" }`,
`stop_tokens` = `<|im_end|>` + `<|endoftext|>`, `sampler_params { type: GREEDY temperature: 0.0 }`,
`max_num_tokens: 2048`, `llm_model_type { qwen3 { } }`, and the Qwen3 jinja chat template in
`jinja_prompt_template`. Build it with `litert_lm_builder.runtime.proto.llm_metadata_pb2` +
`google.protobuf.text_format` (fields introspectable from the descriptors). Pack with
`litert-lm pack --output <run>/work/<name>.litertlm <bundle-dir>`; verify with
`litert-lm describe <bundle>` (prints capabilities + sampler; no engine init).

## §Run (target inference)

```bash
litert-lm run runs/<run-id>/work/<name>.litertlm --no-template --temperature 0 --seed 42 \
  --max-num-tokens 2048 --prompt "<frozen fixture prompt>"
```

Record: engine load time, per-fixture generation time, output text. For exact 32-token caps use the
Python API instead of the CLI (the CLI has no max-new-tokens flag):

```python
import litert_lm.engine as E
from litert_lm import interfaces
engine = E.Engine(model_path=bundle)          # engine init ≈0.5 s (int8 profile)
s = engine.create_session(apply_prompt_template=False,
                          sampler_config=interfaces.SamplerConfig(temperature=0.0, seed=42),
                          max_output_tokens=32)
s.run_prefill([prompt])
for r in s.run_decode_async(): ...            # stream ends at the cap ("Max number of tokens reached")
```

Gotchas recorded during the run: the synchronous `session.run_decode()` fails on this bundle — use
`run_decode_async()`; create **one engine+session per fixture** (sequential sessions in one process
exhaust the engine state pool); engines write an XNNPACK kernel cache
(`<bundle>_<size>.xnnpack_cache`) **beside the bundle** — redirect via `E.Engine(..., cache_dir=...)`
when the bundle lives in a manifest-controlled stage. Active backend: XNNPACK CPU delegate; any
other backend is reported, not assumed. Validation protocol, fixture freezing and staged-reload
rules: [validation.md](validation.md). Packaging and publication:
`scripts/artifact_manifest.py` + `scripts/hub_publish.py`
([huggingface-upload.md](huggingface-upload.md)); huggingface_hub ≥0.34 authenticates via
`HF_TOKEN`.

## §Known limitations

- CPU (XNNPACK delegate) only; GPU/NPU delegates unverified on the recorded host.
- Text-generation only; VLM has no assumed route in LiteRT.
- Context capped at 2048 tokens at this profile (KV cache size is baked into the exported graph);
  longer contexts need their own conversion + acceptance.
- Requires the `mask_as_input`/`transpose_kv_cache` flags (disclosed upstream gap) — re-exporting
  without them yields a non-functional bundle.
- Numerical parity not established at the declared metric (see `recipes.json` evidence).
- No source-build-verified claim: the runtime is a declared official wheel set, verified by
  provenance not by local compilation.
