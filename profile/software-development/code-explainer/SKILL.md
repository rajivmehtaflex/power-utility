---
name: code-explainer
description: Use when building interactive codebase explainers.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: codebase-exploration, html-artifact, project-feature-maintenance, dogfood
  hermes_tags: code-explanation, architecture, visualizer, html-artifact, source-grounded
  platforms: linux, macos, windows
  version: 1.0.0
---

# Interactive Code Explainer

## Overview

Create an interactive visual explanation of a real codebase's execution flow. The deliverable is a self-contained browser artifact that lets a viewer inject or choose a sample prompt, replay its journey through the actual runtime layers, inspect source anchors, and see the final answer or failure path.

The explainer is a deterministic presentation layer. It must be faithful to the repository's source code, but it must not pretend that a static artifact executed the project's live model/runtime unless it actually did.

## When to Use

Use this skill when the user asks to:

- explain a codebase visually;
- create an architecture or execution-flow walkthrough;
- show how a request travels through UI, bridges, workers, runtimes, agents, tools, and results;
- create a demo artifact for a code review, presentation, onboarding, or project showcase;
- inject a sample prompt and show its step-by-step journey.

Do not use it for a plain README, a static architecture image with no interaction, or a live observability dashboard unless the user explicitly asks for those instead.

## Operating Contract

1. **Inspect before inventing.** Trace the actual entrypoint, event handler, bridge, worker, runtime bootstrap, orchestration loop, tools, result path, and failure paths. Never invent symbols, message names, line numbers, or library imports.
2. **Plan before implementation when the user requests a plan.** Save the actionable plan under `.hermes/plans/` with exact files, source anchors, interaction behavior, and verification steps. Do not modify application files during plan-only work.
3. **Keep runtime code separate from the explainer.** Prefer a new artifact under the requested `artifact/` directory. Do not alter the live application merely to produce a static explainer unless live instrumentation is explicitly requested.
4. **Verify in a browser.** A passing static test or HTTP response is insufficient. Navigate to the rendered artifact, inspect the console, exercise the prompt controls and replay, and perform a visual pass.
5. **Do not commit or push unless requested.** Report all generated and modified paths, including untracked artifacts and tests.

## Phase 1: Build the Source Model

Use CodeGraph if available, then confirm important details with direct file reads and searches.

Inspect at minimum:

| Layer | Typical evidence to locate |
|---|---|
| Browser UI | prompt input, submit/run handler, loading state, result/error rendering |
| Main-thread bridge | model/session initialization, user-gesture constraints, pending promises, timeout/error handling |
| Worker | worker message handler, runtime bootstrap, fetch/injection, request/response bridge |
| Runtime | Pyodide/WASM or other runtime initialization and boundary conversions |
| Agent core | dispatch entrypoint, loop, response schema, tool selection, observation append, stop conditions |
| Tools | tool registry, input recovery, execution behavior, error return values |
| Tests/docs | existing behavioral guarantees, expected outputs, known pitfalls |

Produce a compact flow table before authoring the artifact:

| # | Visible step | Runtime owner | Source anchor | Message/payload | Next state |
|---:|---|---|---|---|---|
| 1 | user submits prompt | UI | `path:line` | prompt text | host initialization |
| 2 | session/worker starts | host/worker | `path:line` | message type | runtime ready |
| 3 | agent dispatches | agent core | `path:line` | task id + prompt | ReAct loop |
| 4 | tool or final decision | model/agent | `path:line` | structured response | tool/answer |
| 5 | result returns | bridge/UI | `path:line` | completion/error | rendered output |

Completion criterion: every displayed node and edge has a checked source file/symbol anchor, or is explicitly labeled as a presentation-only connector.

## Phase 2: Define the Prompt Journey

Use a concrete default prompt that exercises the important path. For tool-using agents, prefer a prompt that demonstrates at least one tool call, an observation, another decision, and a final-answer off-ramp.

A proven sample for calculator-plus-summarizer flows is:

> **What is 154 multiplied by 28, and can you summarize that result?**

The representative deterministic trace is:

1. UI captures the prompt during the user action.
2. Host initializes the model session and worker.
3. Worker boots the runtime and injects the agent files/bridges.
4. Python dispatches the task into the ReAct loop.
5. Structured decision selects `calculator` with `154 * 28`.
6. Calculator observation is `4312`.
7. The next decision selects `summarizer` with `The calculation result is 4312.`.
8. Summarizer observation is `Summary (1 total sentences): The calculation result is 4312`.
9. The model selects `none` with a final answer.
10. Completion crosses the bridge and the UI renders the answer.

Label the journey as an **illustrative replay** unless the artifact is connected to a real execution trace. Exact model wording may vary; the static replay must not imply that Gemini/LLM output was captured live.

Include at least these controls:

- editable prompt textarea;
- `Show Journey` / replay button;
- `Use Sample` button;
- reset/restart control;
- preset selector for the happy path and at least one error path;
- previous, next, play/pause, and speed controls;
- clickable diagram nodes that focus the corresponding inspector entry.

For unknown custom prompts, preserve the prompt text but use a clearly labeled generic or selected deterministic trace. Never silently claim that an arbitrary prompt was executed by the live application.

## Phase 3: Author the Artifact

Create a single HTML deliverable under the user's requested folder, normally:

```text
artifact/execution-flow-explainer.html
```

Keep it self-contained:

- inline CSS;
- inline JavaScript;
- inline SVG for the architecture/flow diagram;
- no CDN, external font, remote image, runtime fetch, or backend dependency;
- no Tailwind, Mermaid, D3, or other unbundled external library;
- must work from a local HTTP server and remain usable as a standalone file where browser policy permits.

Use a source-grounded visual structure:

1. **Prompt console** — sample prompt, editable input, presets, replay controls, and an illustrative-replay notice.
2. **Runtime topology** — four swimlanes or equivalent layers, usually UI, main-thread host, worker/runtime, and agent/tools.
3. **Animated state path** — active node and edge highlighting, visited states, and a visible current-step indicator.
4. **Source inspector** — title, runtime owner, source path/line, payload, and why the step matters.
5. **Execution timeline** — one DOM item per state-model step; each item must map to the same index used by JavaScript.
6. **ReAct explainer** — Thought → Action → Observation → context append loop, schema/off-ramp/iteration guardrails.
7. **Failure rail** — initialization, runtime, quota, malformed response, missing input, tool error, timeout, and iteration-limit behaviors where present in the source.
8. **Invariants** — user-gesture constraints, bridge ownership, serialization boundaries, schemas, and tool bounds.

Prefer a data-driven model such as:

```js
const FLOW_STEPS = [
  { id: 'run-agent', node: 'ui-run', source: 'static/index.html:209-220', ... },
  { id: 'host-init', node: 'host-init', source: 'static/js/host_bridge.js:25', ... },
  // ... one object per visible state
];

const DEMO_TRACES = {
  'calculator-summary': {
    prompt: 'What is 154 multiplied by 28, and can you summarize that result?',
    finalAnswer: 'The result is 4312. Summary: The calculation result is 4312',
    overrides: { /* trace-specific payloads and observations */ }
  }
};

function selectTrace(promptText, requestedId) { /* exact preset or generic fallback */ }
```

The static HTML timeline and `FLOW_STEPS` must stay synchronized. If JavaScript has 21 states, render exactly 21 timeline entries, including separate host-resolution and UI-rendering states where both are shown.

For SVG responsiveness, use a flexible width and avoid a desktop-only minimum that clips the rightmost lane:

```css
svg.diagram {
  display: block;
  width: 100%;
  min-width: 0;
  height: auto;
}
```

Add keyboard/focus behavior for diagram buttons and timeline items, `aria-live` status text, semantic headings/regions, readable contrast, and a `prefers-reduced-motion` fallback. Completion criterion: the artifact can be opened at the requested path and the sample prompt is visible without JavaScript before enhancements are applied.

## Phase 4: Add Focused Checks

Add a narrow static smoke test when the repository already uses pytest, normally:

```text
tests/test_artifact_explainer.py
```

Check only durable contract points:

- artifact exists;
- major runtime layers and source filenames appear;
- required message vocabulary appears;
- default sample prompt, `154 * 28`, `4312`, summary observation, and final answer appear;
- happy/error presets and journey controls exist;
- the timeline has the expected number of indexed entries;
- the artifact has inline style/script/SVG and no external dependencies;
- accessibility and reduced-motion hooks exist.

Extract the inline script and run:

```bash
node --check /tmp/execution-flow-explainer.js
```

Use a temporary `hermes-verify-*` script only for focused ad-hoc verification when required by the environment. Place it in the OS-safe temporary directory, run it against the current artifact, print the concrete checks, and delete it in a `finally` block. Call the result **ad-hoc verification**, not a canonical full-suite result.

## Phase 5: Browser Verification

Start a temporary static server from the repository root:

```bash
uv run python -m http.server 8140 --directory <repository-root>
```

Verify readiness with a real HTTP request, then navigate the browser to:

```text
http://127.0.0.1:8140/artifact/execution-flow-explainer.html
```

Perform all of these checks:

1. page title and prompt console render;
2. no browser console errors;
3. `Show Journey` resets to step 1;
4. `Use Sample` restores the calculator/summarizer prompt;
5. preset switching changes prompt, status, and final payload;
6. next/previous and play/pause advance the same state shown in the inspector;
7. the final step renders the expected answer or failure;
8. clicking a diagram node updates the source inspector;
9. the full diagram fits its card at the current viewport or exposes an intentional accessible scroll region;
10. visual inspection confirms no clipped lanes, overlapping labels, unreadable contrast, or broken lower sections.

Stop the temporary server after verification unless the user explicitly asks to keep it running. If the user asks to inspect it, keep it running and provide the verified URL.

## Common Pitfalls

1. **Generic invented architecture** — re-read the actual entrypoints and use exact source anchors.
2. **Calling the replay a live execution** — label deterministic traces as illustrative; state that model responses can vary.
3. **Timeline drift** — keep the static `data-step` list and JavaScript flow array synchronized; include every host/worker/UI state you display.
4. **SVG clipping** — do not use a large desktop `min-width` when the diagram shares a card with an inspector; verify `scrollWidth` versus `clientWidth`.
5. **Broken prompt presets** — after changing a preset, verify both the prompt text and the selected trace id before rendering step 1.
6. **Missing error semantics** — distinguish tool observations, bridge errors, initialization failures, timeouts, and iteration guards.
7. **External asset leakage** — COEP/offline environments can block CDNs; search for `http://`, `https://`, `script src`, and `link href`.
8. **Static-only verification** — curl and pytest do not prove browser behavior; drive the page and inspect the console.
9. **Temporary-server leakage** — use a tracked background process and stop it after the user is finished inspecting.
10. **Scope creep** — do not refactor the runtime or add live telemetry unless requested; the default deliverable is a separate explainer artifact.

## Verification Checklist

- [ ] Source flow inspected and every displayed runtime step has a checked source anchor.
- [ ] Plan saved first when plan mode was requested.
- [ ] Artifact is under the requested `artifact/` folder.
- [ ] Default prompt demonstrates a meaningful tool/observation/final-answer journey.
- [ ] Editable prompt, sample button, presets, replay controls, inspector, and timeline work.
- [ ] Static timeline count matches the JavaScript flow model.
- [ ] Happy path and at least one failure path are represented.
- [ ] Artifact is self-contained and offline-safe.
- [ ] Responsive SVG has no unintended clipping.
- [ ] Focused static checks pass.
- [ ] Inline JavaScript passes syntax checking.
- [ ] Browser page loads with HTTP 200 and no console errors.
- [ ] Browser interactions and final rendered state were exercised.
- [ ] Visual inspection found no overlap, clipping, or contrast failures.
- [ ] Temporary server is stopped unless the user asked to keep it running.
- [ ] Final response names generated files and clearly distinguishes suite results from ad-hoc verification.
