---
name: technical-source-comparison
description: Research current technical announcements, APIs, runtimes, and provider behavior using primary sources, then produce before/after comparisons with explicit route-specific caveats and practical architecture implications.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: get-info
  hermes_tags: research, technical, comparison, primary-sources, APIs, runtimes, deployment
  version: 1.0.0
---

# Technical Source Comparison

## Use when

Use this skill when a user asks to study a technical announcement, compare a platform before and after a change, or reconcile an official capability with what a particular provider, SDK, runtime, or deployment route actually exposes.

Typical triggers:

- “What is new in this announcement?”
- “Compare before and after.”
- “Does this support X?”
- “Why does the UI show a smaller limit than the official documentation?”
- “How does this affect browser, Electron, WASM, or local deployment?”

## Core method

1. **Read the supplied primary source first.** Do not rely on search snippets when the user provides a URL.
2. **Find the authoritative specification or product documentation.** For packaging, use PEP/specification and package-index documentation; for model limits, use the model provider’s API page; for runtime behavior, use the runtime’s source/docs.
3. **Identify the execution route.** Separate model/package identity from provider, authentication mode, API endpoint, SDK/runtime, account entitlement, and client-specific catalog.
4. **Build an evidence map.** Record each material claim with its source, date/version, and whether it is official, implementation-derived, or community-observed.
5. **Produce a before/after table.** Compare workflow, ownership, distribution, compatibility, user experience, and operational burden.
6. **Separate three outcomes:** directly supported, technically possible with adaptation, and not practical/unsupported.
7. **State what did not change.** Announcements often standardize packaging or metadata without changing runtime semantics, security, or OS capabilities.
8. **Explain practical consequences.** Map the change to browser, Electron, WASM, workers, caching, memory, network/CORS, ABI, and fallback architecture where relevant.
9. **Call out uncertainty and contradictions.** If official docs and live/provider metadata differ, explain the route-specific reason and avoid silently choosing one value.
10. **Do not recommend unsafe overrides.** Never advise setting a larger context/compatibility value merely to match a marketing maximum unless the active route has been verified to accept it.
11. **For agent-harness routing requests, inspect both sides of the boundary.** Read the routing system's current deployment/API docs and the harness's provider/custom-model docs. Distinguish an official native integration from a compatible-proxy integration, and state when the proposed path is an inference rather than a documented launcher.
12. **Prefer a virtual-route handoff for compatible harnesses.** When a router exposes OpenAI/Anthropic-compatible endpoints, model the harness as a client of one stable route ID; map that route to configured backend targets, then verify tool-call replay, streaming, session identity, reasoning fields, and served-model observability before recommending production use.

## Local CLI help versus web documentation

Use this subsection when the task asks to execute a CLI's help command, study how to operate it, and compare the result with Internet documentation.

1. **Establish the executable identity first.** Run `command -v <cli>`, `<cli> --version`, and `<cli> --help`. Record the absolute path and version. If the CLI has subcommands, run each `<cli> <subcommand> --help`; help invocations are normally safe, deterministic probes.
2. **Treat local help as the executable contract.** It is the strongest evidence for flags and syntax accepted by the installed binary. Do not recommend a flag merely because a current web page lists it.
3. **Research in two tracks with Exa:** fetch the exact version-tagged documentation/README/changelog for apples-to-apples behavior, and separately inspect the current `latest`/`main` documentation for newer or unreleased additions.
4. **Classify differences explicitly:** exact match; local-only (often an implementation or prose-doc gap); docs-only on the exact version (possible documentation omission); and latest-only (likely version drift). Do not silently treat a latest-page feature as available locally.
5. **Compare operations, not just flags.** Report the command objective, modes, subcommands, examples, state/config locations, authentication behavior, package/resource scopes, trust/security implications, and side effects. Distinguish a package manager used to install the CLI from an application subcommand that manages the application's own packages.
6. **Include a version-aware discrepancy table.** For each mismatch, name the local output, the exact-version source, the current source, and the practical recommendation. State when the local executable should take precedence.
7. **Keep transient setup failures out of the durable lesson.** A missing binary or PATH issue belongs in the execution report, not as a permanent limitation. Preserve only the successful verification pattern (for example, checking the shell path and then running the CLI).

For a reusable evidence-map template and an example of classifying local help against exact-version and latest docs, see `references/cli-help-vs-docs.md`.

## Output structure

Prefer this structure:

1. **Executive answer** — one or two direct paragraphs.
2. **Before vs. after table** — no more than 8–12 high-signal dimensions.
3. **Compatibility/support table** — direct support, indirect route, or unsupported.
4. **What changed / what did not change.**
5. **Practical architecture or migration path.**
6. **Caveats and verification checklist.**
7. **Sources** — prioritize primary documentation, then implementation evidence.

Use exact dates and versions when they affect compatibility. For model limits, distinguish raw context, effective/usable context, and compression thresholds. For package ecosystems, distinguish upload acceptance from successful build, installation, import, and runtime behavior.

## Local model serving route compatibility

When evaluating a local model for an agent stack, separate the roles of the components:

- **Model artifact:** native Transformers checkpoint, GGUF, AWQ/GPTQ/FP8, projector, or draft/speculator files.
- **Inference engine:** vLLM, llama.cpp, SGLang, Transformers, MLX, or another runtime.
- **Agent client/orchestrator:** Prime Agent, Hermes, OpenClaw, or a custom OpenAI-compatible client.
- **Acceleration feature:** draft-model speculation, DFlash, EAGLE/MTP, prefix caching, quantized KV cache, or batching.

Do not infer compatibility from the fact that each component individually supports a related feature. Verify the full tuple: model architecture, weight format, tokenizer/config source, multimodal path, tool-call parser, speculative proposer format, and client API semantics.

For GGUF + vLLM evaluations:

1. Check the current official vLLM GGUF documentation and the out-of-tree GGUF plugin; treat GGUF support as experimental unless the exact model family is covered by end-to-end tests.
2. Inspect the model's `model_type`, `architectures`, tokenizer, projector, and auxiliary draft files. Search the runtime registry and plugin adapters for the exact architecture, not just a similar model family.
3. Distinguish a GGUF-sidecar drafter (often intended for llama.cpp) from a vLLM-compatible `dflash`, `eagle3`, `mtp`, or draft-model proposer. Never assume a `.gguf` draft file can be passed directly to vLLM's speculative configuration.
4. Treat multimodal speculative decoding as a separate compatibility gate. Validate text-only loading, tool calls, image input, then speculation in that order.
5. Validate the agent boundary independently. An OpenAI-compatible endpoint may still emit a model-specific tool-call format that the client cannot parse; check `tool_calls` responses, tool-result replay, reasoning fields, and image content handling.
6. Prefer a route that matches the released artifacts when the goal is local inference. If the model vendor documents llama.cpp/MLX first and vLLM support is experimental, recommend the documented runtime as the baseline and present vLLM as a staged experiment.

For agent workloads, benchmark both baseline and speculative serving at concurrency 1 and representative concurrency. Report acceptance length/rate, end-to-end tokens/sec, time-to-first-token, tool-call latency, memory use, and correctness—not only raw decode speed. See `references/local-serving-route-compatibility.md` for a reusable evidence checklist and route matrix.

## Route-specific model limits

When a model has different limits across routes:

- Use the provider route’s live catalog or API metadata as the operational limit for that route.
- Explain that an official direct-API maximum may not apply to OAuth, Codex, Copilot, OpenRouter, Azure, or another intermediary route.
- Inspect the client’s resolver/source when possible to determine precedence: explicit config, live provider metadata, cached metadata, or fallback constants.
- Treat stale fallback constants as a maintenance risk, not as proof of the true provider limit.
- Distinguish Hermes’ own compression threshold from the provider’s maximum context.

## Browser/WASM package analysis

For Pyodide/PyEmscripten-style packaging:

- Pure-Python wheels are the easiest path.
- Native C/C++/Rust extensions must be cross-compiled for the exact ABI/platform tag and all native dependencies must also be compatible.
- Separate “can upload to an index” from “can install/import/run in the target runtime.”
- Check for threads/pthreads, multiprocessing, subprocess/fork, sockets, OS-specific APIs, GUI/terminal modules, OpenSSL assumptions, GPU-driver APIs, dynamic linking, and architecture-specific SIMD.
- Remember that a packaging standard does not add OS capabilities to WebAssembly.
- Recommend a capability gateway and worker isolation for untrusted Python; do not expose unrestricted filesystem/network/process access.

## Evidence and formatting rules

- Use Exa for current web research when requested or when current facts matter.
- Prefer direct fetches of supplied URLs and official documentation.
- Do not present community reports as official facts; label them as implementation evidence or observed behavior.
- If the user asks for tabular output, include URLs as readable hyperlinks and avoid hiding important caveats in prose.
- Include a short “bottom line” that answers the decision the user is actually making.

## Linked references

- `references/gpt56-route-context.md` — example evidence map for reconciling direct OpenAI context limits with Codex-route metadata.
