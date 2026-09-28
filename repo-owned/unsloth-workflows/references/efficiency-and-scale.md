# Efficiency, scale, and quantization

## High-performance kernels and packing

- **Unsloth Triton Kernels**: Hand-crafted forward and backward kernels for cross-entropy loss, RoPE embedding, RMSNorm, and LoRA projections eliminate PyTorch autograd overhead and maintain exact numerical accuracy.
- **Padding-Free Sample Packing**: Packs sequences to eliminate pad tokens, achieving up to 3x training speedup while preserving sequence attention masks across example boundaries.
- **Gradient Checkpointing**: Unsloth's selective activation offloading allows fine-tuning larger batch sizes without out-of-memory (OOM) failures.

## Quantization paradigms

- **Dynamic 3.0 GGUFs & Dynamic Quants**: Employs adaptive bit-rate allocation per layer based on KL divergence and perplexity sensitivity, outperforming standard static/imatrix GGUF quantization.
- **Dynamic 1.58-bit (Ternary) Quants**: Enables running frontier reasoning models like DeepSeek-R1 locally with near-lossless accuracy at minimal memory footprint.
- **Dynamic NVFP4**: Blackwell native 4-bit floating-point execution providing massive throughput improvements on RTX 50 series and B200 hardware.

## Multi-GPU distributed training

When scaling beyond a single GPU, choose the distribution strategy deliberately:
1. **Distributed Data Parallel (DDP)**: Use the Unsloth CLI for multi-GPU training. Each GPU maintains a full model replica and processes an independent data batch, synchronizing gradients via NCCL.
2. **Fully Sharded Data Parallel (FSDP)**: Shards parameters, gradients, and optimizer states across GPUs, required when the model and optimizer cannot fit within a single GPU's VRAM.
3. **Pipeline / Model Splitting (`device_map="balanced"`)**: Shards layers across devices sequentially. Recommended for inference evaluation; inefficient for active training due to pipeline bubbles.

Sources: [packing and kernels](https://unsloth.ai/docs/blog/3x-faster-training-packing.md), [multi-GPU guide](https://unsloth.ai/docs/basics/multi-gpu-training-with-unsloth.md), [DDP via CLI](https://unsloth.ai/docs/basics/multi-gpu-training-with-unsloth/ddp.md), [Dynamic 3.0 GGUFs](https://unsloth.ai/docs/basics/dynamic-3.0-ggufs.md), [NVFP4 guide](https://unsloth.ai/docs/basics/nvfp4.md), [DeepSeek-R1 1.58-bit](https://unsloth.ai/docs/models/tutorials/deepseek-r1-how-to-run-locally/deepseek-r1-dynamic-1.58-bit.md).
