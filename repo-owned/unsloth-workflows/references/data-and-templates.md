# Data and chat templates

## Supported dataset formats

Built-in data validation and runner scripts support two standard text structures:

1. **ChatML / Conversational**:
   ```json
   {"messages":[{"role":"user","content":"question"},{"role":"assistant","content":"answer"}]}
   ```
2. **Alpaca Format**:
   ```json
   {"instruction":"task description","input":"optional context","output":"target response"}
   ```

### Specialized & multimodal schemas (Prepare Mode)
- **Unsloth Studio Data Recipes**: Interactive and recipe-based dataset transformation, column mapping, synthetic filtering, and cleaning.
- **Tool Calling & Agent Trajectories**: Records containing tool declarations, structured assistant `tool_calls`, and environment `tool` responses.
- **Vision / Multimodal**: Conversational records embedding image inputs alongside text prompts for vision-language fine-tuning (e.g. Qwen-VL, Gemma-Vision).

## Validation rules

Before any GPU initialization or training occurs:
1. Validate required fields, non-empty assistant content, and strictly valid JSONL structure.
2. Deduplicate records and identify potential token-length outliers.
3. Validate train and evaluation sets in pairs to prevent data contamination or train/eval overlap.
4. Keep explicit held-out evaluation splits on disk; do not perform random or silent in-memory splits during execution.

## Chat templates and loss masking

The tokenizer's chat template serializes roles, delimiters, and end-of-turn tokens into the raw token sequence.
- **Template Consistency**: Mismatches between training template and inference template cause looping, hallucinations, or premature EOS. Retain the exact template across training, evaluation, and export.
- **Response-Only Loss Masking**: Calculate gradients solely on target responses (`train_on_responses_only`) while masking prompt/system tokens. Ensure mask logic preserves at least one valid response token per sample to prevent zero-loss trainer stalls.

Sources: [datasets guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/datasets-guide.md), [chat templates](https://unsloth.ai/docs/basics/chat-templates.md), [Data Recipes](https://unsloth.ai/docs/new/studio/data-recipe.md), [tool calling guide](https://unsloth.ai/docs/basics/tool-calling-guide-for-local-llms.md).
