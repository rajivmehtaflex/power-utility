# Data and chat templates

Built-in records are either ChatML:

```json
{"messages":[{"role":"user","content":"question"},{"role":"assistant","content":"answer"}]}
```

or Alpaca-style `instruction`, optional `input`, and `output`. Validate required fields, roles, non-empty assistant outputs, malformed JSON, exact duplicates, and train/eval overlap before GPU work. Keep an explicit held-out evaluation file; never split silently during execution.

The tokenizer’s chat template serializes roles into the token sequence. A correct schema with the wrong template can produce poor or looping inference. Assistant-only loss masks the prompt while training response tokens; a mask that removes all response tokens produces zero loss. Preserve the same template and EOS behavior through export and serving.

Source: [datasets](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/datasets-guide.md) and [chat templates](https://unsloth.ai/docs/basics/chat-templates.md).
