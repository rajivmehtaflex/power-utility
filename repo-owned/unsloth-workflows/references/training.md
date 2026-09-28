# SFT, LoRA/QLoRA, QAT, CPT, and checkpoints

## Adaptation methods

- **LoRA**: Freezes base model weights and trains rank-decomposition matrices across attention and MLP projections.
- **QLoRA**: Loads the base model in 4-bit NormalFloat (NF4) while maintaining LoRA adapters in 16-bit precision, significantly reducing VRAM footprint.
- **Quantization-Aware Training (QAT)**: Simulates 4-bit quantization during fine-tuning, allowing weights to adapt to quantization noise and recovering full 16-bit accuracy upon export.
- **Continued Pretraining (CPT)**: Trains on unstructured domain or language text. Requires balanced data mixtures and modest learning rates to avoid catastrophic forgetting of general reasoning capabilities.
- **Multi-Token Prediction (MTP)**: Trains auxiliary prediction heads concurrently with the main language model, enabling native speculative decoding and accelerated inference.

## Hyperparameter guidelines

- **Rank & Alpha**: Default to rank $r=16$ or $r=32$. Set $\alpha = r$ or $\alpha = 2r$.
- **Target Modules**: Target all major linear projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`).
- **Dropout**: Keep `lora_dropout = 0` to enable Unsloth's optimized custom Triton kernels.
- **Gradient Checkpointing**: Use `use_gradient_checkpointing = "unsloth"` to reduce activation memory by up to 70% with negligible recomputation overhead.
- **Learning Rate**: Typically `2e-4` for QLoRA SFT on small/medium models; lower to `5e-5` for full fine-tuning or sensitive CPT runs.

## Context length and throughput

- **500K Long-Context Fine-Tuning**: Unsloth kernels handle ultra-long contexts with memory-efficient RoPE scaling and gradient accumulation.
- **Kernels + Packing**: Packs multiple variable-length training examples into a single contiguous context window, eliminating padding token waste and delivering up to 3x throughput improvements while strictly preserving sequence boundary isolation.

## Checkpoint management

- Distinguish between loading a LoRA adapter (weights only) and resuming training from a checkpoint (`resume_from_checkpoint`), which restores optimizer states, lr scheduler, and RNG states.
- Save intermediate checkpoints at deterministic step boundaries (`save_steps`) to ensure crash resilience.

Sources: [hyperparameters guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide.md), [continued pretraining](https://unsloth.ai/docs/basics/continued-pretraining.md), [QAT](https://unsloth.ai/docs/blog/quantization-aware-training-qat.md), [500K context length](https://unsloth.ai/docs/blog/500k-context-length-fine-tuning.md), [packing and kernels](https://unsloth.ai/docs/blog/3x-faster-training-packing.md), [MTP guide](https://unsloth.ai/docs/models/mtp.md).
