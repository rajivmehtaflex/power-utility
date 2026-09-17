# Preferences, RL, and specialized modalities

DPO, ORPO, KTO, and SimPO use preference or desirability data. GRPO generates groups of attempts and updates the policy using a reward function. Reward hacking is a first-class failure mode: a higher measured score may not mean the intended behavior improved. Use a bounded smoke run before longer RL.

Vision workflows add image content to messages and may selectively train vision, language, attention, or MLP layers. TTS/STT workflows require aligned audio/text and model-specific sampling rates or special tokens. Embedding workflows optimize vector representations and pooling behavior rather than chat responses. MoE models require architecture-aware memory and routing checks.

For these paths, read the current official example, check installed APIs, adapt a task-specific script, and label the result as documented or tested. Source: [RL guide](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide.md), [vision](https://unsloth.ai/docs/basics/vision-fine-tuning.md), [TTS](https://unsloth.ai/docs/basics/text-to-speech-tts-fine-tuning.md), and [embeddings](https://unsloth.ai/docs/basics/embedding-finetuning.md).
