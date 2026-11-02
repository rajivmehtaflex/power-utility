---
name: hf-model-evaluator
description: Use when evaluating any Hugging Face model URL, collection link, or repo ID, or checking whether a model fits local hardware (RAM, VRAM, Disk) and Colibri/GGUF engines.
license: Apache-2.0
compatibility: Python 3.8+ with standard library; optional hf CLI for downloading and authentication.
metadata:
  author: rajivmehtaflex
  version: "1.0.0"
---

# Hugging Face Model & Collection Hardware Evaluator

## Overview

This skill allows coding agents to inspect any model repository or collection from Hugging Face, determine its parameter count, quantization format, and weight sizes, probe local system resources (CPU RAM, NVIDIA GPU VRAM, free disk), and evaluate whether it can run locally.

It maps models directly to **Colibri** native engines (*From RAM* vs *Streaming experts from SSD*), GGUF runtimes (`coli import`, `llama.cpp`), or generic runners (`vLLM`).

---

## When to Use This Skill

Activate this skill when:
* The user provides a Hugging Face URL (e.g. `https://huggingface.co/Qwen/Qwen2.5-Coder-32B` or `hf.co/...`).
* The user provides a Hugging Face Collection URL (`https://huggingface.co/collections/...`).
* The user asks: *"Can my machine run model X?"* or *"How much RAM/VRAM do I need for this model?"*
* The user asks if Colibri or GGUF supports a specific model on Hugging Face.

---

## Workflows

### 1. Environment & Pre-Flight Check

Before evaluating models, you can verify that the environment, hardware probes, and Hugging Face network access are functional:

```bash
python3 scripts/check_hf_model.py --check-env
```

To receive machine-readable data for automated decisions:
```bash
python3 scripts/check_hf_model.py --check-env --json
```

### 2. Evaluating a Single Model

To inspect a single Hugging Face model (by URL or `org/repo` ID):

```bash
# By URL
python3 scripts/check_hf_model.py https://huggingface.co/puwaer/DeepSeek-V4-Flash-0731-reap-150b

# By repo ID
python3 scripts/check_hf_model.py Kreuzzelg/qwen36-35b-a3b-colibri-i4-gs64
```

### 3. Evaluating a Hugging Face Collection

To batch-evaluate all models inside a Hugging Face collection:

```bash
python3 scripts/check_hf_model.py https://huggingface.co/collections/LiquidAI/lfm3-6adc03dcfe62bfd2fcd8eea7
```

### 4. Machine-Readable Agent Integration (`--json`)

When you need to parse the result programmatically:

```bash
python3 scripts/check_hf_model.py <model-or-collection> --json
```

The JSON response contains:
* `environment`: Total and available RAM, free disk, GPU VRAM, driver, compute capability, and `hf` CLI status.
* `model`: Architecture, MoE configuration, download size, GGUF variants.
* `assessment`:
  * `status`: `PASS`, `TIGHT`, `NEEDS_RAM`, or `NEEDS_DISK`.
  * `fits`: Boolean flag indicating if the model can execute on this machine.
  * `execution_mode`: `from RAM / VRAM` or `streams experts from SSD (Colibri MoE)`.
  * `colibri_supported`: Boolean flag.
  * `recommended_commands`: Exact CLI commands (`hf download`, `coli import`, `coli setup`) to install and run the model.

---

## Hardware Fit Reference

| Status | Meaning | Action for Agent |
| :--- | :--- | :--- |
| **`PASS`** | Model fits comfortably in memory and disk. | Recommend proceeding with setup or conversion commands. |
| **`TIGHT`** | Meets minimum RAM/disk thresholds, but optimal cache headroom is low. | Warn user that performance or batch size may be limited. |
| **`NEEDS_RAM`** | Insufficient system RAM for the model's dense layers or full weights. | Suggest a smaller quantized variant (e.g., GGUF Q4_K_M) or an MoE architecture. |
| **`NEEDS_DISK`** | Insufficient free storage space to download weights. | Advise user to free disk space or specify an external drive. |

---

## Colibri Execution Modes

* **From RAM**: The entire model (all layers and experts) fits into system RAM. Yields maximum generation speed without disk I/O bottlenecks.
* **Streams Experts from SSD**: Colibri pins the dense core (~4-15 GB) in RAM, and dynamically streams activated MoE experts from NVMe storage on each token.
* **GGUF Import**: If GGUF files are present in the repository, Colibri can import and run them directly using:
  ```bash
  python3 c/coli import <model.gguf>
  ```
