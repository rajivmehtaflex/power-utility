# SFT, LoRA/QLoRA, CPT, and checkpoints

SFT learns from desired responses. LoRA freezes the base model and trains low-rank adapter matrices. QLoRA combines LoRA with a 4-bit base to reduce memory. Full fine-tuning updates the model broadly and costs substantially more memory; use it only when adapter capacity is insufficient.

Start with 1–3 epochs, a learning rate near `2e-4` for ordinary LoRA/QLoRA, rank 16 or 32, dropout 0, all major attention/MLP linear modules, and an effective batch size that fits memory. Tune from evidence, not defaults.

Continued pretraining uses raw text and can teach a domain or language. It needs careful mixing so useful base capabilities are retained. Save checkpoints and record the optimizer/trainer state when resume semantics matter; loading only a LoRA adapter resumes weights, not necessarily optimizer state.

Source: [hyperparameters](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide.md) and [continued pretraining](https://unsloth.ai/docs/basics/continued-pretraining.md).
