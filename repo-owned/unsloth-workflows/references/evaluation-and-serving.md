# Evaluation, export, and serving

Compare the original model and adapter on held-out examples. Report loss only with the exact split and masking used; report task metrics or generation samples for user-facing behavior. Evaluate exported and quantized artifacts again.

An adapter requires its compatible base model. A merged model incorporates adapter weights. GGUF is a runtime-oriented format for llama.cpp-compatible engines. QLoRA training, dynamic post-training quantization, and quantization-aware training are different operations.

The most common post-export failures are an incorrect chat template, EOS token, or start-of-sequence behavior. Reload the artifact and perform a short generation before calling export verified. Supported serving routes include Unsloth inference, llama.cpp, Ollama, LM Studio, vLLM, and SGLang, subject to model/runtime compatibility.

Source: [deployment](https://unsloth.ai/docs/basics/inference-and-deployment.md), [GGUF](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf.md), [dynamic GGUF](https://unsloth.ai/docs/basics/dynamic-3.0-ggufs), and [troubleshooting](https://unsloth.ai/docs/basics/troubleshooting-and-faqs.md).
