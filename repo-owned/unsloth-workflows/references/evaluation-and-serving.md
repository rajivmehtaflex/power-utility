# Evaluation, export, serving, and agent integration

## Evaluation and verification

- **Held-Out Evaluation**: Always benchmark baseline and trained adapter models on isolated test sets using identical sequence masking and chat templates. Report full-sequence loss, exact match, and sample generations.
- **Export Verification**: Never assume an export succeeded solely because files were written. Reload merged weights or adapters, configure inference mode, and run a smoke-test generation to verify prompt delimiters and EOS tokens.

## Export formats

- **LoRA Adapter**: Compact weight-delta files (`save_pretrained`) requiring the base model at inference time.
- **Merged 16-bit**: Merges adapter weights into the base model (`save_pretrained_merged`), outputting standard Hugging Face Safetensors.
- **GGUF**: Formats weights for llama.cpp, Ollama, and LM Studio (`save_pretrained_gguf`) using standard or Dynamic 3.0 quantization.

## Local serving and remote access

- **Local API Server**: Unsloth provides a local OpenAI- and Anthropic-compatible HTTP endpoint supporting streaming, vision inputs, and tool calling.
- **Python SDK & HTTP Client**: Query the local endpoint directly with the official OpenAI or Anthropic Python SDKs or standard `curl`.
- **LAN Sharing & Cloudflare Tunnels**: Expose local endpoints across local area networks or configure zero-trust Cloudflare tunnels for secure remote access.
- **Production Serving**:
  - *vLLM*: High-throughput multi-request serving with LoRA hot-swapping and continuous batching.
  - *SGLang*: Optimized for complex multi-turn prompting and structured constrained decoding.
  - *llama-server*: Speculative decoding support for 2x faster token generation.

## Agent runtime and mobile deployment

- **Coding Agent Integrations**: Direct drop-in compatibility as the local LLM backend for Claude Code, OpenAI Codex, Hermes Agent, OpenClaw, and OpenCode.
- **Model Context Protocol (MCP)**: Connect local models running under Unsloth to external MCP servers for tool and resource orchestration.
- **Mobile Deployment**: Export models to ExecuTorch for on-device local execution on iOS and Android devices.

Sources: [inference & deployment](https://unsloth.ai/docs/basics/inference-and-deployment.md), [saving to GGUF](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf.md), [API endpoint](https://unsloth.ai/docs/basics/api.md), [LAN serving](https://unsloth.ai/docs/basics/lan.md), [vLLM guide](https://unsloth.ai/docs/basics/inference-and-deployment/vllm-guide.md), [Claude Code guide](https://unsloth.ai/docs/basics/claude-code.md), [Hermes Agent integration](https://unsloth.ai/docs/integrations/hermes-agent.md), [MCP guide](https://unsloth.ai/docs/basics/mcp.md), [mobile deployment](https://unsloth.ai/docs/basics/inference-and-deployment/deploy-llms-phone.md).
