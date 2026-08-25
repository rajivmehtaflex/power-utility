# Local serving route compatibility: GGUF + agent client

Use this reference when a user wants to combine a newly released local model, a quantized artifact, an inference server, speculative decoding, and an agent client.

## Evidence checklist

Record these independently before recommending a stack:

| Layer | Evidence to collect |
|---|---|
| Model identity | `model_type`, `architectures`, parameter count, tokenizer, chat template |
| Artifact | Exact files, byte sizes, projector files, draft/speculator files, quantization labels |
| Runtime | Official supported-model registry, plugin adapters, end-to-end tests |
| Multimodal path | Vision processor/projector support and image API semantics |
| Tools | Runtime tool-call parser, emitted response shape, tool-result replay |
| Speculation | Runtime proposer method, compatible draft checkpoint format, vocabulary/hidden-size constraints |
| Client | API type, reasoning fields, developer/system role behavior, image/tool support |
| Workload | Concurrency, context length, output length, latency and memory targets |

## Muse Glimmer / vLLM case study

The Muse Glimmer GGUF repository exposes:

- `muse-glimmer-30B-kquant-17gb.gguf`
- `muse-glimmer-30B-kquant-dynamic.gguf`
- `mmproj-kquant.gguf`
- `dflash-kquant.gguf`

The model metadata identifies a custom `muse_glimmer` architecture and a multimodal conditional-generation model. The GGUF repository's DFlash and projector files are sidecars; their presence does not prove compatibility with vLLM's DFlash proposer or multimodal engine path.

Current vLLM documentation says GGUF support is experimental and is provided through the out-of-tree `vllm-gguf-plugin`. The plugin's tested-coverage table is not evidence that arbitrary vLLM-supported architectures work; exact GGUF tensor mappings and model-specific adapters still matter. Search the current vLLM registry and plugin source for the exact architecture before claiming support.

The correct staged order is:

1. Load the target text model.
2. Verify normal generation and tokenizer/chat-template behavior.
3. Verify OpenAI-style tool calls and tool-result replay.
4. Verify image input with the projector.
5. Add speculative decoding with a runtime-compatible proposer.
6. Connect the agent client and benchmark end-to-end behavior.

Do not jump directly to `method=dflash` with an arbitrary `.gguf` sidecar. Confirm that the draft file has the format, config, vocabulary, and proposer interface expected by the installed vLLM version.

## Prime Agent boundary

Prime Agent can register a local vLLM, Ollama, LM Studio, or other OpenAI-compatible endpoint through `~/.prime/agent/models.json` using `api: "openai-completions"`. This makes Prime Agent an inference client, not a speculative-decoding implementation.

For a custom local endpoint, explicitly set compatibility flags when appropriate:

- `supportsDeveloperRole: false` if the server accepts `system` but not `developer`.
- `supportsReasoningEffort: false` if the server does not accept OpenAI `reasoning_effort`.
- Set `input: ["text"]` until image handling is verified.
- Set a conservative `contextWindow` rather than copying a marketing maximum.

An OpenAI-compatible HTTP surface is not enough for agent reliability. Confirm that the server returns a structured `tool_calls` array. A model-specific XML/ATEM tool format may require a server parser or compatibility adapter before Prime Agent can execute tools.

## Benchmark fields

For sequential agent workloads, compare baseline and speculative serving at concurrency 1 and representative concurrency. Capture:

- time-to-first-token
- decode tokens/sec
- accepted tokens per speculative step
- acceptance rate
- end-to-end tool-call latency
- memory and KV-cache use
- error/retry rate
- task correctness

Speculative decoding may help low-concurrency, memory-bound reasoning workloads, but raw tokens/sec alone is not sufficient. Tool calls, short outputs, multimodal preprocessing, and parser failures can dominate end-to-end latency.

## Primary references

- vLLM GGUF documentation: https://docs.vllm.ai/en/latest/features/quantization/gguf/
- vLLM speculative decoding documentation: https://docs.vllm.ai/en/latest/features/speculative_decoding/
- vLLM GGUF plugin: https://github.com/vllm-project/vllm-gguf-plugin
- Prime Agent custom model configuration: https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/models.md
- Prime Agent provider documentation: https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/providers.md
