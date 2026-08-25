# Local LLM Setup for Hermes Agent

Ollama and llama.cpp provide on-device / on-server LLM inference for Hermes, eliminating API costs and enabling fully private operation.

## Ollama Setup (Recommended)

### Install
```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
```

### Pull a model (choose by RAM)
```bash
ollama pull qwen3.5:32b     # 32GB+ RAM — best quality
ollama pull qwen3.5:14b     # 16GB RAM — good balance
ollama pull gemma4:12b      # Alternative
ollama pull qwen2.5-coder:7b # 8GB RAM — minimum viable
```

### Configure Hermes
```bash
hermes config set model.provider custom
hermes config set model.default qwen3.5:14b
hermes config set model.base_url http://127.0.0.1:11434/v1
```

### Keep model loaded in memory (reduces latency)
```bash
curl http://127.0.0.1:11434/api/generate \
  -d '{"model":"qwen3.5:14b","keep_alive":"24h"}'
```

## llama.cpp Setup (Maximum Performance)

### Build on Debian
```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -DGGML_OPENMP=OFF
cmake --build build --config Release -j$(nproc)
```

### Start server
```bash
./build/bin/llama-server \
  --jinja -fa \
  -c 32768 \
  -ngl 99 \
  -m models/qwen2.5-coder-32b-instruct-Q4_K_M.gguf \
  --port 8080 --host 0.0.0.0
```

### Configure Hermes
```bash
hermes config set model.provider custom
hermes config set model.default ggml-org/gemma-4-26B-A4B-it-GGUF:Q4_K_M
hermes config set model.base_url http://127.0.0.1:8080/v1
```

## Model Sizing by RAM

| RAM | Max Model | Context Window | Use Case |
|---|---|---|---|
| 4 GB | 0.5B-1B (Q4_K_M) | 1024-2048 | Chat only |
| 6 GB | 1.5B-2B (Q4_K_M) | 2048-4096 | Basic agent |
| 8 GB | 3B (Q4_K_M) | 2048-4096 | Simple skills |
| 16 GB | 7B-14B (Q4_K_M) | 4096-8192 | Full agent |
| 32 GB | 14B-32B (Q4_K_M) | 8192-32768 | Complex tasks |
| 64 GB+ | 32B-70B (Q4_K_M) | 32768+ | Near-cloud quality |

## Mobile Benchmarks (tokens/second)

| Model | Quant | Snapdragon 855 | Newer SoCs (8 Gen 3) | RAM |
|---|---|---|---|---|
| Qwen2.5-0.5B | Q5_K_M | 16 tok/s | ~30+ tok/s | ~850 MB |
| Qwen2.5-1.5B | Q3_K_M | 7.6 tok/s | ~25 tok/s | ~1.3 GB |
| Gemma 3-1B | Q4_K_M | ~5 tok/s | 14 tok/s | ~1.2 GB |
| Llama 3.2-3B | Q4 | ~8 tok/s | ~30 tok/s | ~3 GB |
| Qwen3-0.6B | Q8_0 | ~10 tok/s | 17-19 tok/s | ~640 MB |

> Usability threshold: 5+ tok/s feels interactive, 10+ responsive, 20+ fast.

## Critical Constraint: Tool Calling

Hermes's agent loop requires the model to emit structured function calls.

| Model Size | Tool Calling | Agent Usability |
|---|---|---|
| 0.5B-1B | Unreliable | Chat only |
| 1.5B-3B | Works for simple tools | Basic agent tasks |
| 4B-7B | Good | Most skills work |
| 7B+ (Q4) | Strong | Full agent experience |

**Recommended for Hermes agent loop:** Qwen 4B-7B minimum, 14B+ for complex multi-step tasks.

## Cloud Fallback (Hybrid)

```yaml
# ~/.hermes/config.yaml
model:
  default: qwen3.5:14b
  provider: custom
  base_url: http://127.0.0.1:11434/v1

fallback_providers:
  - provider: openrouter
    model: anthropic/claude-sonnet-4
  - provider: zai
    model: glm-5.2
```

Local model tries first; cloud activates only when local fails or times out.

## Termux / Android Path

Ollama has a native Termux package: `pkg install ollama`.

The `ollama-termux` fork (DioNanos/ollama-termux) is purpose-built for Android ARM64 with:
- Prebuilt binaries (no compilation)
- CPU thread tuning (big cores only)
- Auto flash attention
- Auto context window limiting by RAM
- Explicit Hermes Agent launcher: `ollama launch hermes`

## Sources

- Hermes Ollama guide: https://hermes-agent.nousresearch.com/docs/guides/local-ollama-setup
- HuggingFace local agents: https://huggingface.co/docs/hub/main/en/agents-local
- Ollama-Termux: https://github.com/DioNanos/ollama-termux
- Academic benchmarks: https://arxiv.org/html/2410.03613v1
