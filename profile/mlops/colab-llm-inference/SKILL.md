---
name: colab-llm-inference
description: Use when running LLM inference on Colab GPUs.
metadata:
  author: Hermes Curator
  tags: colab, gpu, llm, inference, quantization, vram
  version: 1.0.0
---

# Colab LLM Inference

Run large language models on Google Colab GPUs reliably — from VRAM estimation to quantized loading and verification. Captures the non-obvious Colab-specific pitfalls uncovered in live sessions (e.g., Gemma-4 12B on T4).

## When to Use

- User asks "will model X fit on Colab T4/L4/A100?" or "does Y fit with quantization/MTP/QAT?"
- Loading any 7B+ model on Colab and need to choose BF16 vs INT8 vs 4-bit
- `transformers` load fails with `unexpected keyword argument 'load_in_4bit'` or `AmbiguousGlobalPerLayerAttributeError`
- `nvidia-smi` or `torch.cuda.is_available()` disagrees between `ssh` and `colab exec`
- `pip install llama-cpp-python` hangs and leaves BUSY/defunct kernel

## VRAM Estimation (Rule of Thumb)

```
weights_GB = params * bytes_per_param / 1e9   # BF16=2, INT8=1, INT4=0.5
total_VRAM ≈ weights_GB * 1.05 + KV_overhead  # KV: 6GB for 2k ctx BF16, ~3GB for 4-bit
```

| Precision | Bytes/param | Example: 12B model | Fits T4 15GB? | Fits A100 40GB? |
|-----------|-------------|-------------------|---------------|-----------------|
| BF16 | 2 | 23.9GB → ~30GB total | ❌ | ✅ |
| INT8 | 1 | 12GB → ~16GB | ❌ borderline | ✅ |
| Q4_0/NF4 | 0.5 | 6GB → ~9GB | ✅ | ✅ |

Use `hf models info REPO_ID` (`safetensors.parameters.BF16`) to get exact params, then apply formula. See `references/gemma4-t4-fit.md` for full Gemma-4 numbers.

## Quantized Loading — Correct Pattern for Gemma-4 (and any `Gemma4Unified*`)

**Never** pass `load_in_4bit=True` as a top-level kwarg to `AutoModelForImageTextToText.from_pretrained` — Gemma4's `__init__` rejects it:

```
TypeError: Gemma4UnifiedForConditionalGeneration.__init__() got an unexpected keyword argument 'load_in_4bit'
```

**Correct (bitsandbytes wheel, 60s install, no compile):**

```python
from transformers import AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig
import torch

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)
processor = AutoProcessor.from_pretrained("google/gemma-4-12B-it", trust_remote_code=True)
model = AutoModelForImageTextToText.from_pretrained(
    "google/gemma-4-12B-it",
    device_map="auto",
    quantization_config=quant_config,
    trust_remote_code=True,
)
# Live on T4: 7573 MiB used, 7GB free, 5.2 tok/s for 120 tokens
```

**Why not `llama-cpp-python`?** `pip install llama-cpp-python` on Colab triggers a source compile (>10 min), often hangs, leaves `python3 <defunct>` (zombie) visible via `ssh ... "ps aux"` and a persistent `BUSY (exec(...))` that `colab restart-kernel` doesn't clear. Recovery requires `colab stop -s NAME && colab new -s NAME --gpu T4`. Prefer `bitsandbytes==0.47.0` wheel.

**Why not `compressed-tensors` NVFP4 path?** `unsloth/gemma-4-12b-it-NVFP4` fails with `AmbiguousGlobalPerLayerAttributeError: 'num_key_value_heads' is per-layer` due to version mismatch. Use `BitsAndBytesConfig` path above.

## GPU Visibility: `colab exec` vs `ssh` (Critical)

- **`colab exec -s NAME -f script.py`** → runs **inside the kernel container** where CUDA is mounted. `torch.cuda.is_available() == True`, `nvidia-smi` shows `Tesla T4 15360 MiB`.
- **`ssh g-xxx "python3 -c '...'"`** → lands in **host VM's root FS** where `libnvidia-ml.so` is not in PATH. `nvidia-smi` fails (`couldn't find libnvidia-ml.so`), `torch.cuda.is_available() == False`.

**Live proof 2026-08-23 (`g-gemma-4-12b` T4):**
- `colab exec`: `cuda True, Tesla T4, 7573 MiB used after 4-bit load`
- `ssh`: `False, NVIDIA-SMI couldn't find libnvidia-ml.so`

**Implication:** Always run GPU inference/training via `colab exec`. VSCode Remote-SSH's integrated terminal is also host-FS, so wrap model runs in `colab exec`.

## Colab SSH Alias with Custom Session Name

When user requests alias == session name (e.g., `g-gemma-4-12b`):

```sshconfig
Host g-gemma-4-12b
  HostName colab-runtime
  User root
  ProxyCommand /usr/bin/env PYTHONPATH= /Users/rajivmehtapy/.local/share/uv/tools/mighty-colab/bin/mighty-colab ssh --proxy-mode -s g-gemma-4-12b
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  RequestTTY no

Host g-gemma-4-12b-shell
  HostName colab-runtime
  User root
  ProxyCommand /usr/bin/env PYTHONPATH= /Users/rajivmehtapy/.local/share/uv/tools/mighty-colab/bin/mighty-colab ssh --proxy-mode -s g-gemma-4-12b
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  RequestTTY yes
```

Must start with `/usr/bin/env PYTHONPATH=` (Hermes leaks `PYTHONPATH` → `ModuleNotFoundError: pydantic_core._pydantic_core`). Use absolute `mighty-colab` path from `readlink -f $(which colab)`.

## Workflow Checklist

1. `export PYTHONPATH="" && colab --auth=adc new -s NAME --gpu T4`
2. `colab --auth=adc status -s NAME` → verify `Hardware: T4`
3. `colab --auth=adc exec -s NAME -f install.py` → install `bitsandbytes transformers accelerate`
4. Estimate VRAM via `hf models info` + formula; pick quantized repo if needed
5. Load with `BitsAndBytesConfig` pattern above via `colab exec`
6. Verify: `nvidia-smi` inside exec vs ssh discrepancy expected
7. `colab stop -s NAME` when done (billing)

## References

- `references/gemma4-t4-fit.md` — full 2026-08-23 session transcript
- `references/colab-exec-vs-ssh.md` — exec vs ssh GPU visibility reproduction
