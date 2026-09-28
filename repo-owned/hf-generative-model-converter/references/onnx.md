# ONNX recipe — Optimum export + ONNX Runtime (declared official wheel)

Verified tuple this recipe documents: `Qwen/Qwen3-0.6B` @ `c1899de289a04d12100db370d81485cdf75e47ca`
(decoder-only, text-generation) → ONNX fp32 (`text-generation-with-past`), Linux x86_64 **CPU**,
optimum-onnx `0.1.0` / optimum `2.1.0` / onnxruntime `1.30.0` / transformers `4.57.6`. All values
below come from recorded evidence in `assets/recipes.json` (recipe
`onnx-qwen3-0.6b-linux-x64-cpu`). Other models/platforms need their own recipe row with their own
evidence — never reuse this page's pins for a different tuple.

**Scope:** text-generation only. VLM ONNX export is a deferred row (2026-09-28 scope decision) —
do not attempt it under this recipe and never advertise ONNX as VLM-verified.

## §Toolchain — locked env, declared runtime

This route has **no native build**. The runtime (`onnxruntime`) is a **declared official PyPI
wheel**: first-party (Microsoft), MIT, version-pinned and hash-recorded. The source policy forbids
*silent* prebuilt binaries — a declared wheel with recorded provenance is the sanctioned form.
Provenance evidence recorded for the verified run:

- wheel `onnxruntime-1.30.0-cp312-cp312-manylinux_2_28_x86_64.whl`
  sha256 `fa688e7891a6aa206636fe7372e27ee75fd17713289f6b4fc7b190e0a7de9328`
  (<https://pypi.org/project/onnxruntime/1.30.0/#files>)
- installed native library verified byte-identical to the wheel payload
  (`onnxruntime_pybind11_state.cpython-312-x86_64-linux-gnu.so`
  sha256 `0b2a6e0d6dfe7fdb04e8ddefb488f69f3c90b7552a148b0c42ff3f28a3c2b33b`)
- `hf-xet` excluded via `override-dependencies = ["hf-xet; sys_platform == 'never'"]` (binary
  policy covers optional native Hub transfer extensions)

**Environment** (uv project; lock sha256 `dfbf268e9db7c04970fb2b2e85bf736fa33760e3eb9784514229fb2404a317c0`):

```toml
dependencies = [
    "torch==2.11.0",        # declared CPU index (pytorch-cpu), same as the GGUF env
    "numpy~=2.2.6",
    "transformers==4.57.6", # same pin as the GGUF env — parity fairness
    "sentencepiece>=0.1.98,<0.3.0",
    "protobuf>=4.21.0,<5.0.0",
    "huggingface_hub>=0.34.0,<1.0",
    "optimum~=2.1.0",
    "optimum-onnx==0.1.0",
    "onnxruntime==1.30.0",
    "onnx>=1.18,<2",
]
```

`uv lock` + `uv sync --locked`; record the lock's sha256 (it feeds the env build key
`sha256(commit ‖ pyproject ‖ lock)[:16]` — recorded key `37261dde718f24a3`). Keep the venv directory
name stable after `uv sync`: console entry points embed absolute interpreter paths (a rename breaks
`optimum-cli`; the recorded workspace keeps a compatibility symlink).

**Support check before converting** (registration is decorator-driven; import the config module
first or the mapping reads empty):

```bash
python -c "
import optimum.exporters.onnx.model_configs  # triggers @register_tasks_manager_onnx
from optimum.exporters.tasks import TasksManager
m = TasksManager.get_supported_tasks_for_model_type('qwen3', 'onnx', library_name='transformers')
assert 'text-generation-with-past' in m, m
print('supported')"
```

## §Acquire — pinned model, verified

Reuse or re-acquire exactly the pinned revision (resumable snapshot; the recorded run reused the
GGUF round's local snapshot and verified it first):

```bash
python -c "
from huggingface_hub import snapshot_download
print(snapshot_download('Qwen/Qwen3-0.6B', revision='c1899de289a04d12100db370d81485cdf75e47ca',
                        local_dir='runs/<run-id>/work/model'))"
```

Integrity gate used by the recorded run: `sha256(model.safetensors)` must equal the LFS oid at the
pinned revision (`f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`, checked via
`/api/models/Qwen/Qwen3-0.6B/tree/<revision>`). License Apache-2.0, public, not gated — status
`clear`.

## §Convert

Freeze fixtures and thresholds **before** running this (see [validation.md](validation.md)); the
recorded run froze 3 prompts + token-set Jaccard ≥ 0.5 before any export existed.

```bash
optimum-cli export onnx \
  -m runs/<run-id>/work/model \
  --task text-generation-with-past \
  --dtype fp32 \
  --device cpu \
  runs/<run-id>/work/onnx
```

- Expected output inventory: `model.onnx` (graph) + `model.onnx_data` (external fp32 weights,
  ≈3.0 GB) plus processor sidecars (`tokenizer.json`, `tokenizer_config.json`, `vocab.json`,
  `merges.txt`, `added_tokens.json`, `special_tokens_map.json`, `chat_template.jinja`,
  `config.json`, `generation_config.json`). Anything else at staging time fails the manifest.
- The exporter prints its own torch-vs-ONNX max-diff check; treat nonzero exit as a blocked tuple.

## §Run (target inference)

```python
from optimum.onnxruntime import ORTModelForCausalLM
import onnxruntime

model = ORTModelForCausalLM.from_pretrained("runs/<run-id>/work/onnx")
# Declared patch (see below): required for qwen3 until an optimum release honors explicit head_dim
model.embed_size_per_head = model.config.head_dim
out = model.generate(**enc, max_new_tokens=32, do_sample=False, num_beams=1)
```

Record the active provider — `CPUExecutionProvider` expected on this host; any other provider is
reported, not assumed. **Do not skip the patch line** without checking `config.head_dim`:

> **Upstream gap (disclosed):** optimum 2.1.0 sizes the KV cache as
> `hidden_size // num_attention_heads` (=64) for qwen3 instead of the model's explicit
> `config.head_dim` (=128); only gemma/gpt_oss/nemotron are honored upstream. The exported graph is
> correct — without the patch the first decode step fails with
> `INVALID_ARGUMENT ... past_key_values ... Got: 64 Expected: 128`. The recorded run applies a
> one-attribute load patch and discloses it in `recipes.json`, the package `model-card.md` and
> `EVIDENCE.md`.

## §Validation and packaging

Protocol, fixture freezing and staged reload rules: [validation.md](validation.md). The recorded run:
functional smoke passed (coherent, factually correct output; near-limit fixture token-identical to
the reference); **numerical fidelity failed at the declared threshold** (Jaccard
0.300 / 0.171 / 1.000) and is disclosed, not relaxed; staged reload passed byte-identically
(`HF_HUB_OFFLINE=1`, cwd `/`). Package the `§Convert` inventory plus `LICENSE` (Apache-2.0 from the
source repo), `model-card.md` and `EVIDENCE.md`; build/verify the manifest with
`scripts/artifact_manifest.py` and publish with `scripts/hub_publish.py` (rules:
[huggingface-upload.md](huggingface-upload.md)). Note: with huggingface_hub ≥0.34 the publish
helpers authenticate via `HF_TOKEN` (or the stored token file); the deprecated
`HUGGINGFACEHUB_API_TOKEN` name is no longer read.

## §Known limitations

- CPU (`CPUExecutionProvider`) only; GPU/other providers unverified on the recorded host.
- Text-generation only; VLM ONNX is a deferred row — no exporter/loader evidence exists.
- Requires the declared `embed_size_per_head` patch until the upstream optimum gap is fixed.
- Numerical parity not established at the declared metric (see `recipes.json` evidence).
