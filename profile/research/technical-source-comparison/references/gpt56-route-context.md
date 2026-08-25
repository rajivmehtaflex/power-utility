# Route-specific context-window evidence: GPT-5.6 Luna example

This reference records a reusable investigation pattern, not a permanent model limit.

## Evidence pattern

- OpenAI direct API model documentation lists GPT-5.6 Luna with a 1.05M context window and 128K max output.
- Hermes uses provider-aware context resolution. For `openai-codex`, it probes the Codex model catalog endpoint and treats the returned `context_window` as authoritative for the active route.
- The same model slug can therefore expose a different operational window through Codex OAuth, ChatGPT/Codex, OpenRouter, Copilot, Azure, or another intermediary.
- Hermes’ compression threshold is separate from the provider maximum. With a 50% threshold, a 372K route window triggers normal compression around 186K tokens; a client/provider may also expose a lower effective percentage.
- Hermes source may retain fallback constants that lag the live provider catalog. If the UI shows a newer value, live metadata likely won; if live probing fails, stale fallback data can reappear.

## Verification checklist

1. Identify the active session model and provider, not only `~/.hermes/config.yaml`.
2. Check whether the current chat was started before a configuration/model change; existing sessions retain their model.
3. Read the direct provider model page for the advertised maximum.
4. Inspect the active route’s model catalog/API metadata.
5. Inspect client resolver precedence and fallback constants.
6. Avoid forcing a larger `context_length` unless the active route has been verified to accept it.
7. Report raw provider context, effective usable context, and Hermes compression threshold separately.

## Sources used in the original investigation

- OpenAI GPT-5.6 Luna model page: https://developers.openai.com/api/docs/models/gpt-5.6-luna
- OpenAI model catalog: https://developers.openai.com/api/docs/models
- Hermes model configuration: https://hermes-agent.nousresearch.com/docs/user-guide/configuring-models
- Hermes context compression: https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching
