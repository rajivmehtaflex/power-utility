# Setting Default Provider & Model via Config

## Shorthand Format

The `model.default` setting accepts a shorthand format that automatically sets both provider and model:

```bash
# Shorthand: provider/model
hermes config set model.default "openrouter/google/gemma-2-9b-it"

# Explicit: set provider and model separately
hermes config set model.provider openrouter
hermes config set model.default "google/gemma-2-9b-it"
```

When using the shorthand `provider/model` format:
- The provider is automatically inferred from the first segment
- The model ID is the remainder
- Both `model.provider` and `model.default` are updated

## Common OpenRouter Free Models

| Model ID | Provider | Notes |
|----------|----------|-------|
| `openrouter/google/gemma-2-9b-it` | openrouter | Gemma 2 9B IT - good general purpose |
| `openrouter/deepseek/deepseek-v4-pro` | openrouter | DeepSeek V4 Pro - coding focused |
| `openrouter/qwen/qwen3.5-32b-instruct` | openrouter | Qwen 3.5 32B - large context |
| `openrouter/meta-llama/llama-3.1-8b-instruct` | openrouter | Llama 3.1 8B - fast, efficient |
| `openrouter/mistral/mistral-small-3.2-24b-base` | openrouter | Mistral Small 3.2 |

## Verification

After setting, verify the configuration:

```bash
hermes config get model.default
hermes config get model.provider
```