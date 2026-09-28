# Preferences, Reinforcement Learning, and specialized modalities

## Preference optimization and RL

Unsloth supports both preference alignment and reward-driven reinforcement learning:

- **Preference Optimization (DPO, ORPO, KTO, SimPO)**: Align models on paired chosen/rejected examples or desirability scores without an active reward environment.
- **Group Relative Policy Optimization (GRPO)**: Generates groups of responses per prompt and scores them relative to group mean and standard deviation. Removes the separate value/critic network, slashing VRAM by over 50% compared to traditional PPO.
- **GRPO with 7x Longer Context**: Optimized attention kernels and sequence parallel rollouts allow training DeepSeek-R1 style reasoning models with long context windows.
- **GSPO (Group Sequence Policy Optimization)**: Sequence-level policy optimization for structured step-by-step reasoning.
- **Vision RL (VLM RL)**: Reinforcement learning directly on multimodal models, rewarding visual grounding, diagram comprehension, and spatial accuracy.
- **FP8 RL**: Accelerates rollout generation and policy updates under 8-bit floating point precision.
- **Training AI Agents with RL**: Rewards multi-step tool calls, terminal task success, and valid API usage.
- **Mitigating Reward Hacking**: A higher reward score does not imply better behavior. Combine verification of exact outputs, strict format penalties (e.g. `<think>` XML blocks), and length penalties to avoid degenerate or verbose loops.
- **Precision: FP16 vs BF16 for RL**: Upstream findings demonstrate FP16 overcomes training-inference mismatch issues present in BF16 when generating rollouts.

## Specialized modalities and architectures

- **Vision / Multimodal**: Fine-tune models like Qwen3-VL, Gemma-Vision, and DeepSeek-OCR 2. Supports freezing the vision encoder while training cross-attention projections or the full language backbone.
- **12x Faster MoE Fine-Tuning**: Custom Triton kernels optimize token routing and dispatch for Mixture-of-Experts architectures (e.g., DeepSeek-V3/V4, Qwen-MoE).
- **TTS and Audio**: Fine-tuning voice and speech recognition models with tokenized spectrograms.
- **Embeddings**: Fine-tuning vector embedding models with InfoNCE or Matryoshka representation loss.

Sources: [RL guide](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide.md), [GRPO long context](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/grpo-long-context.md), [Vision RL](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/vision-reinforcement-learning-vlm-rl.md), [FP8 RL](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/fp8-reinforcement-learning.md), [GSPO RL](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/advanced-rl-documentation/gspo-reinforcement-learning.md), [FP16 vs BF16 for RL](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/advanced-rl-documentation/fp16-vs-bf16-for-rl.md), [Agent RL](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/training-ai-agents-with-rl.md), [Faster MoE](https://unsloth.ai/docs/basics/faster-moe.md).
