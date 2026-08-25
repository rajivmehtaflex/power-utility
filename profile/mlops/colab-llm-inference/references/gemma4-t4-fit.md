# Gemma-4 12B on Colab T4 — Live Fit Transcript (2026-08-23)

Session: `g-gemma-4-12b` | Endpoint: `gpu-t4-s-kkb-use1c0-1wkq3jq4047mh` (also earlier `gpu-t4-s-kkb-usw4a1-2ghm7px79b1z6`) | Hardware: Tesla T4 15360 MiB | CUDA 13.0 | Driver 580.82.07 | torch 2.11.0+cu128

## Model Sizes (via `hf models info`)

```
google/gemma-4-12B-it
  safetensors.parameters.BF16 = 11959730224 (11.96B)
  used_storage = 23-78GB (single file 23.9GB, 23.9 = 11.96B*2)
  single safetensor: model.safetensors 23.9GB

google/gemma-4-12B-it-qat-q4_0-gguf
  file: gemma-4-12b-it-qat-q4_0.gguf 6.97GB
  total 11,907,350,576 params

google/gemma-4-12B-it-qat-w4a16-ct
  used_storage 10,296,399,522 (~10GB)

unsloth/gemma-4-12b-it-NVFP4
  used_storage 9,337,135,790 (~9.3GB)
  safetensors: F32 288, BF16 1.06B, F8_E4M3 2.9B, U8 4.2B = 8.2B total
```

## VRAM Math

- BF16: 11.96B*2 = 23.9GB weights (22.3 GiB) + 6GB KV/overhead = ~29.4GB total → OOM on T4 (15GB), needs A100 40GB
- Q4_0: 5.6 GiB weights + 3GB = ~8.8GB → fits T4 with ~6GB free
- Live measured 4-bit: 7573 MiB used (see below)

## Failed Path 1 — `unsloth/gemma-4-12b-it-NVFP4` with compressed-tensors

```
Loading model (device_map=auto, torch_dtype=bfloat16)...
model.safetensors: downloading bytes: | 0.00B / 9.30GB
FAILED: 'num_key_value_heads' is a per-layer attribute and may vary across layers.
  ...
  File ".../compressed_tensors/utils/helpers.py", line 464, in get_num_kv_heads
    if hasattr(config, "num_key_value_heads"):
  File ".../transformers/integrations/heterogeneity/configuration_utils.py", line 298
    raise AmbiguousGlobalPerLayerAttributeError(...)
transformers.integrations.heterogeneity.configuration_utils.AmbiguousGlobalPerLayerAttributeError
```

Root cause: `compressed-tensors` version mismatch with heterogeneous `per_layer_config` in Gemma-4. Don't use this path for Gemma-4 until upstream fixes.

## Failed Path 2 — `load_in_4bit=True` kwarg

```
model = AutoModelForImageTextToText.from_pretrained(..., load_in_4bit=True, ...)
TypeError: Gemma4UnifiedForConditionalGeneration.__init__() got an unexpected keyword argument 'load_in_4bit'
```

Fix: use `quantization_config=BitsAndBytesConfig(...)`.

## Failed Path 3 — `llama-cpp-python` compile

```
pip install llama-cpp-python
# hangs >10 min, leaves:
USER PID %CPU %MEM STAT COMMAND
root  66  1.0  0.0  Z  [python3] <defunct>
Status: BUSY (exec(/tmp/install_llamacpp.py))
colab restart-kernel  → stays BUSY
Recovery: colab stop -s g-gemma-4-12b && colab new -s g-gemma-4-12b --gpu T4
```

Prefer `bitsandbytes==0.47.0` wheel (61.3 MB at 20.7 MB/s, 60s).

## Successful Path — `BitsAndBytesConfig` NF4

```python
from transformers import AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig
quant_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4")
processor = AutoProcessor.from_pretrained("google/gemma-4-12B-it", trust_remote_code=True)
model = AutoModelForImageTextToText.from_pretrained("google/gemma-4-12B-it", device_map="auto", quantization_config=quant_config, trust_remote_code=True)
```

**Live output:**

```
Processor done in 4.5s
Loading model (device_map=auto, torch_dtype=bfloat16)...
Loading weights: 0%| 0/677
model.safetensors: downloading ... (streaming, ~60s for 23.9GB)
Model loaded in 97.3s
Model on device: cuda:0

GPU after load:
Sun Aug 23 05:09:27 2026
| 0 Tesla T4 Off | 00000000:00:04.0 Off | 0 |
| N/A 58C P0 29W / 70W | 7573MiB / 15360MiB | 0% |
...
7573, 7340, 15360  (used, free, total)

Generation in 23.30s (5.2 tok/s):
user: Explain quantum computing in one paragraph, simple terms.
model: Quantum computing is a type of computing that uses the principles of quantum mechanics...
→ SUCCESS
```

Install that worked:

```
pip install -q bitsandbytes==0.47.0 transformers accelerate huggingface_hub
# 61.3/61.3 MB 20.7 MB/s, returncode 0, 60s
bitsandbytes 0.47.0, transformers 5.15.0, torch 2.11.0+cu128 cuda True
```

## Disk

```
Filesystem Size Used Avail Use% Mounted on
overlay 113G 48-57G 57-66G 42-51% /
```

Both 23.9GB BF16 and 7-9GB quantized fit on disk.

## Conclusion

- T4 15GB: BF16 ❌, 4-bit ✅ (live 7.5GB)
- Use `BitsAndBytesConfig` NF4 double-quant path for Gemma-4 on Colab T4
- Avoid `compressed-tensors` NVFP4 and `llama-cpp-python` compile on Colab
