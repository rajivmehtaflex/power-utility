# Framework map

Unsloth is an acceleration and workflow layer spanning PyTorch, Transformers, Hugging Face Datasets, PEFT, TRL, and local inference/serving engines.

## Ecosystem architecture

- **Unsloth Core**: Fast training kernels (cross-entropy, LoRA, RoPE, RMSNorm, GeLU), custom backends (FlashAttention, SDPA, xFormers), memory-efficient packing, and quantization runtime.
- **Unsloth Studio & Unsloth Desktop**: Cross-platform application (Linux, macOS, Windows) providing a local UI for dataset preparation (Data Recipes), interactive fine-tuning, model export, and local chat.
- **Serving & Agent Runtime**: Built-in OpenAI/Anthropic-compatible local HTTP API server, LAN sharing, Cloudflare tunnel access, and direct integrations with coding agent environments (Claude Code, OpenAI Codex, Hermes Agent, OpenCode, OpenClaw, Hugging Face Jobs).

## Lifecycle

**model + tokenizer → dataset + chat/tool template → learning objective → parameter method & precision → optimized training → evaluation → export/quantization → serving/agent runtime**

Learning objective and parameter method remain strictly independent:
- **Learning objectives**:
  - *CPT (Continued Pretraining)*: Raw domain or language text to adapt foundational representations.
  - *SFT (Supervised Fine-Tuning)*: Structured demonstrations (ChatML, Alpaca, tool calling, vision).
  - *Preference Optimization*: Ranked or binary preferences (DPO, ORPO, KTO, SimPO).
  - *Reinforcement Learning*: Rule-based or model-based reward scoring (GRPO, GSPO, VLM RL, Agent RL).
  - *Quantization-Aware Training (QAT)*: Fine-tuning under simulated 4-bit precision to eliminate quantization loss.
  - *Multi-Token Prediction (MTP)*: Training auxiliary heads for faster speculative decoding.
  - *Specialized*: Embedding models and voice/audio (TTS/STT).
- **Parameter methods & precision**: Full fine-tuning (FFT), LoRA, QLoRA (4-bit base), FP8, BF16/FP16, and Dynamic NVFP4.

Begin with a compact instruct model (e.g. 0.5B to 8B class) and QLoRA unless hardware capacity or a specific workload demands another approach.

## Dynamic documentation queries

Upstream documentation at `https://unsloth.ai/docs/llms.txt` is published via GitBook and supports live, agent-directed question answering. If specific syntax or undocumented flags are needed, query dynamically:
```
GET https://unsloth.ai/docs/docs.md?ask=<specific_question>
```

Sources: [fine-tuning guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide.md), [datasets guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/datasets-guide.md), [Unsloth Desktop](https://unsloth.ai/docs/desktop.md), [Unsloth Studio](https://unsloth.ai/docs/new/studio.md), [LLMs.txt catalog](https://unsloth.ai/docs/llms.txt).
