# CLI/library execution-flow replay recipe

Use this reference when the target is an agent harness, SDK, service library, or CLI rather than a browser application.

## Source model

Start at the runnable host surface, not an imagined UI:

```text
input()/API handler
  -> composition root or builder
  -> config/provider adapter
  -> context/session assembly
  -> core loop
  -> tool schema + registry execution
  -> observation append or final off-ramp
  -> history/memory persistence
  -> printed/API result
```

Check each transition against source. If a project has Protocol seams but passes raw provider clients, registries, or memory objects into an underlying runtime, show that concrete-object boundary explicitly. If the runtime is an editable sibling dependency, inspect the sibling implementation for loop and stop-condition semantics, but do not modify it for the explainer.

## Deterministic replay design

Prefer the repository's deterministic eval fixtures over invented model output:

- A scripted client should provide the response fields the loop actually reads, including stop reason and token usage when observers consume them.
- For a tool path, use the fixture's sequence: assistant `tool_use` → registry execution → `tool_result` appended to working messages → assistant text with no tool uses.
- For an error path, use the fixture's real unknown-tool or tool-exception text and iteration-limit response.
- Time-dependent tools should use the deterministic fake output from tests, not a made-up current timestamp.
- Label the whole UI an illustrative replay; preserve custom prompt text but route it to an explicit generic/preset trace unless a live trace is actually captured.

## Artifact checks

Keep a narrow static check in the project's existing test convention. For repositories using `evals/deterministic/`, put the explainer smoke test there rather than creating a parallel `tests/` hierarchy. Prefer non-importing checks for the artifact so editable sibling packages, provider SDKs, and environment state cannot prevent collection.

Durable checks include source filenames/anchors, flow-step count, preset/error vocabulary, inline CSS/JS/SVG, no external assets, and accessibility/reduced-motion hooks. Extract inline JavaScript and run `node --check` using the environment's actual Node executable.

## Isolated ad-hoc verification

When a separate verification script is required, create it with `tempfile.NamedTemporaryFile(prefix="hermes-verify-", dir=<OS-safe-temp-dir>, delete=False)`. Have it read the current artifact and run concrete assertions; create any extracted JavaScript temp file with the same prefix. Remove both files in `finally` blocks. If running under an isolated `env -i` PATH, pass the absolute path to user-managed executables such as Node. Report the result as **ad-hoc verification**, not as a canonical suite result.

## Worked harness pattern

A typical composable harness explainer can show:

1. REPL reads and strips a message.
2. `build()` wires provider, context, loop, tools, optional MCP, and memory.
3. `run_turn()` builds system context and a bounded history window.
4. The loop calls the raw provider client with tool schemas.
5. The registry executes a registered tool safely; errors become model-visible text.
6. Tool results are appended as observations, or no tool use takes the natural final-answer exit.
7. The iteration guardrail returns a failure reply when `max_iterations` is reached.
8. The session records the exchange and the host prints the reply.

Treat lane names as presentation groupings unless the repository has actual process boundaries matching them.
