# Source-Grounded Visual Explainers

Use this recipe when a user wants to understand a codebase through an animated HTML explainer, an execution diagram, or a visual implementation plan.

## 1. Establish the evidence boundary

Start with the current code, not a design document:

```bash
codegraph status -j
codegraph files
codegraph explore "complete execution flow from UI entry point through boundaries, orchestration, tools, completion, and errors"
```

Record:

- index freshness: `pendingChanges`, `worktreeMismatch`, indexed file count;
- source files and symbols on the happy path;
- message/event names at every asynchronous boundary;
- retry, timeout, and terminal-error branches;
- tests that cover the behavior;
- older docs that may describe a superseded design.

If CodeGraph returns only the most relevant files, follow up with targeted queries for the missing entry point, bridge, worker, tool registry, and tests. Do not infer full coverage from one capped exploration result.

## 2. Build a canonical flow model

Use one data structure as the source for the diagram, timeline, inspector, and tests. A useful step shape is:

```js
{
  id: "llm-request-1",
  lane: "main-thread",
  title: "Prompt API request",
  symbol: "PromptChainHost.handleWorkerMessage",
  source: "static/js/host_bridge.js:35-58",
  messageType: "LLM_REQUEST → LLM_RESPONSE",
  payload: "prompt + responseConstraint",
  why: "The main thread owns the LanguageModel session.",
  next: "agent-parse-1",
  failureNext: "llm-error-1"
}
```

Every visual node should have:

- a stable key;
- a real file/symbol/line anchor;
- a runtime lane or boundary;
- a call, event, or message label;
- a short explanation of the invariant it demonstrates;
- an explicit next step and, when relevant, failure destination.

Model the full path, not only the central loop:

```text
UI event
  → initialization/user-gesture gate
  → host/session boundary
  → worker bootstrap
  → WASM/Python loading
  → orchestrator dispatch
  → LLM request/response bridge
  → tool decision
  → tool execution
  → observation appended to context
  → repeat or final-answer off-ramp
  → completion/error propagation
  → UI rendering
```

## 3. Prefer a deterministic replay for a standalone artifact

Unless the user explicitly requests live instrumentation, use a deterministic replay seeded with a representative prompt and known tool outcomes. The artifact should explain the real runtime without executing the real model or worker.

State this plainly in the page: “This is a source-grounded replay of the current execution path, not a live model trace.” This prevents a polished animation from being mistaken for observed runtime telemetry.

If live instrumentation is later requested, treat it as a separate feature: define an event schema, preserve event ordering and task IDs, add timeouts/error reporting, and verify the real browser path end-to-end.

## 4. Design the visual language

For a single-file HTML artifact:

- use inline SVG for lanes, nodes, edges, markers, and loop diagrams;
- put edges behind nodes and keep coordinates on regular lane/rank grids;
- use semantic colors rather than rainbow coding: active/hot path, success, failure, and inactive;
- show message types on edges and source paths on nodes or the inspector;
- keep the diagram horizontally scrollable on narrow screens;
- use CSS keyframes for packet/pulse animation and honor `prefers-reduced-motion`;
- use OS-native fonts and inline CSS/JS so the file works offline.

The artifact should have two synchronized representations:

1. a topology/swimlane diagram for “where execution moves”; and
2. a timeline/inspector for “what this step does and which source proves it.”

Controls such as Play/Pause, Previous, Next, Restart, speed, and node click must all call the same `renderStep(index)` function. Never maintain separate highlight state for the timeline and diagram.

### Sample-prompt journey pattern

When the explainer is meant to be demonstrated, put an editable prompt console above the diagram and seed it with one representative prompt. Use a local trace registry rather than invoking the live model:

```js
const DEMO_TRACES = {
  calculatorSummary: {
    prompt: "What is 154 multiplied by 28, and can you summarize that result?",
    overrides: {
      "calculator-action": 'calculator("154 * 28")',
      "calculator-observation": "4312",
      "summarizer-observation": "Summary (1 total sentences): The calculation result is 4312"
    },
    finalAnswer: "The result is 4312. Summary: The calculation result is 4312"
  }
};
```

Provide `Show Journey`, `Use Sample`, `Reset`, and at least one alternate preset such as a direct-answer off-ramp or tool-error path. `selectTrace(prompt, presetId)` should choose an exact preset when the prompt matches, otherwise use an explicit generic trace; never imply arbitrary text was executed by Gemini. Reset the selected trace to step zero and update the status/inspector immediately. Label the experience as an **illustrative replay** and state that exact model responses can vary.

### Synchronization and responsive invariants

Treat the canonical flow model and the HTML fallback timeline as one contract:

- `FLOW_STEPS.length` must equal the number of static timeline items;
- `data-step` values must be contiguous (`0..N-1`), with no missing terminal host-resolution or UI-render steps;
- every `renderStep(index)` access must have a corresponding timeline item, SVG node, and inspector payload;
- static tests should assert the exact step sequence, not only a minimum count. A count-only test can miss an off-by-one bug that overwrites the final UI row;
- after adding a terminal step, run the replay to the end and inspect the final answer row.

For responsive SVG diagrams, do not leave a desktop `min-width` larger than the diagram card unless horizontal scrolling is intentional and visibly usable. At the primary viewport, measure `scrollWidth` against `clientWidth` (or verify the intended scroll affordance on narrow screens) and visually inspect the rightmost lane; a clipped lane can be missed when the left half looks correct.

If a browser ref click reports success but the rendered state does not change, verify the event binding in the page context with a DOM click such as `document.getElementById("next-step").click()` and then inspect the progress/inspector state. Treat the resulting DOM state as interaction evidence, not as a substitute for a full browser-path check.

## 5. Keep content useful without JavaScript

Put the default narrative, timeline labels, runtime lanes, and at least one step’s details in ordinary HTML. JavaScript should enhance the page, not be the only place content exists.

Add:

- a default active step on load;
- semantic headings and landmarks;
- an `aria-live` status for the selected step;
- keyboard shortcuts with visible focus styles;
- SVG `<title>` and `<desc>`;
- text labels in addition to color;
- a static explanation that remains readable with JavaScript disabled.

## 6. Validate in two layers

### Static checks

Use a focused test to assert:

- the artifact exists;
- required runtime lanes, source anchors, and message types are present;
- inline `<style>`, `<script>`, and `<svg>` exist;
- no external CDN, font, image, Mermaid, D3, or Tailwind dependency is referenced;
- reduced-motion handling exists.

Then run the project’s normal test suite. Do not make the visual artifact test dependent on Gemini Nano, Pyodide download, Chrome flags, credentials, or network access.

For last-mile evidence when a full suite is not the requested check, create a short OS-safe temporary verification script with `tempfile.NamedTemporaryFile(prefix="hermes-verify-")`, run it against the current artifact, and delete it in `finally`. Report it as **ad-hoc verification**; do not call the canonical full suite green based on this focused script.

### Browser/rendered checks

Static HTML validity cannot catch diagram geometry or interaction bugs. Open the rendered artifact and verify:

- arrows reach the intended nodes;
- node text and source labels do not overflow;
- failure paths are distinguishable from the happy path;
- the inspector, timeline, and diagram stay synchronized;
- Play/Pause/Next/Previous/Restart/speed work without duplicate timers;
- keyboard navigation works;
- reduced motion removes travel/pulses without removing meaning;
- mobile layout is readable and scrollable;
- the browser console has no uncaught errors;
- the page still conveys the execution path when JavaScript is disabled.

## Common mistakes

- Treating one capped CodeGraph response as proof that the entire repository was indexed.
- Letting an old playbook override current on-disk source.
- Drawing a visually convincing path that has no file/symbol/message evidence.
- Calling an animated replay “live execution.”
- Making all content appear only from a `render()` function.
- Using independent state machines for timeline and SVG highlights.
- Skipping browser visual verification because static tests pass.
- Adding the artifact to runtime code when the user only requested an explainer.
