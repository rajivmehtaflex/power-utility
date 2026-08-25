# Agent-harness router integration reference

Use this reference when evaluating a model router such as NVIDIA NeMo Switchyard with an agent harness such as Pi.

## Evidence pattern

- Switchyard's native server exposes OpenAI Chat Completions, OpenAI Responses, and Anthropic Messages endpoints.
- A Switchyard route has a client-visible semantic `id`; the route maps internally to configured targets and upstream model IDs.
- Pi supports custom providers through `~/.pi/agent/models.json`, including `openai-completions`, `openai-responses`, and `anthropic-messages`.
- Therefore, the practical Pi integration is a compatible-proxy boundary: Pi selects one stable virtual route ID, while Switchyard performs backend selection.
- Do not describe this as an official native Pi launcher unless the current Switchyard docs explicitly list Pi. The documented launcher set may be narrower than the proxy API's compatibility surface.

## Switchyard strategy mapping

| Need | Route strategy | Caveat |
|---|---|---|
| Strong model for exploration/errors, efficient model for steady edits | `stage_router` | Depends on tool-result/progress history reaching the proxy. |
| Classify initial task difficulty | `llm_classifier` | Adds a judge call; structured JSON verdict must be in assistant content. |
| Start weak, escalate after repeated trouble | Escalation mode | Requires stable session identity for streak/latch behavior. |
| Guaranteed strong planning route | `passthrough` to capable target | Planning artifact/handoff remains an agent-harness concern. |

For `stage_router`, `capable_first` is the safer initial recommendation for coding; `efficient_first` is cost-first and should be treated as a deliberate quality trade-off.

## Pi boundary checks

Before calling the integration production-ready, verify:

1. Pi can list and select the virtual route through `models.json`.
2. A non-streaming completion succeeds through the route.
3. Streaming text is parsed correctly.
4. Tool calls arrive in the format Pi expects and tool results replay successfully.
5. The router receives enough conversation/tool-result history for its selected algorithm.
6. Session identity is preserved when using affinity or escalation routing.
7. Reasoning fields and provider-specific thinking controls do not break normal assistant content or tool-call parsing.
8. Switchyard stats or routing logs identify the actual served target, since Pi may display only the virtual route.
9. A trusted fallback exists for routing, context overflow, provider errors, and malformed judge output.

## Configuration shape

A native Switchyard deployment separates:

- `llm_clients`: upstream base URL, wire format, credential environment variable.
- `targets`: upstream model IDs and client references.
- `routes`: client-visible route IDs and routing algorithms.

Pi's provider configuration points at the local Switchyard base URL and declares the route ID as a custom model. Keep secrets in environment variables or the harness/router credential store, not in committed configuration.

## Source set

Primary evidence used for this reference:

- NVIDIA NeMo Switchyard repository and `docs/core_concepts.md`.
- Switchyard `docs/getting_started.md`, `docs/cli_reference.md`, and routing algorithm docs.
- Pi coding-agent `docs/models.md`, `docs/extensions.md`, and `docs/sdk.md`.
- NVIDIA's article, “Route AI Agent Workloads Across Models with NVIDIA NeMo Switchyard.”
