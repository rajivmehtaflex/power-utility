# Efficiency and scale

Unsloth’s kernels, Flash/SDPA/xFormers backends, padding-free execution, and packing reduce wasted work. Packing must preserve example boundaries. Gradient checkpointing trades extra computation for lower activation memory. Precision is a quality and compatibility choice: FP16/BF16/FP8 and 4-bit paths depend on the GPU and model.

For multiple GPUs, distinguish DDP (replicated models and synchronized gradients), FSDP (sharded training state), and model splitting (`device_map="balanced"`). More GPUs do not automatically create one larger-memory GPU. Long-context training increases activation and kernel pressure; validate the chosen length with a small run.

Source: [packing and kernels](https://unsloth.ai/docs/blog/3x-faster-training-packing.md), [multi-GPU](https://unsloth.ai/docs/basics/multi-gpu-training-with-unsloth.md), and [QAT](https://unsloth.ai/docs/blog/quantization-aware-training-qat.md).
