---
name: subagent-orchestration
description: Decompose implementation plans into parallel-safe task waves and dispatch them via delegate_task to maximize Hermes subagent concurrency. Covers wave decomposition, dependency graphs, module API contracts, and dispatch patterns.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: plan, simplify-code
  hermes_tags: subagents, parallel, delegation, orchestration, waves, delegate-task, concurrency
  platforms: linux, macos, windows
  version: 1.0.0
---

# Subagent Orchestration

Use this skill when executing a plan (or ad-hoc multi-step work) through `delegate_task` with maximum parallelism. It covers how to **decompose tasks into waves**, define **module API contracts** for parallel safety, draw **dependency graphs**, and **dispatch** the right number of subagents per wave.

The `plan` skill (protected built-in) writes the plan; this skill governs how to **restructure and execute** that plan for parallel subagent dispatch.

## When to Use

- User says "optimize for subagents," "parallelize," "utilize Hermes capacity," "use subagents"
- A plan has 4+ independent tasks that write different files
- You want to cut wall-clock time by 40–60% via concurrency
- You're about to call `delegate_task` with `tasks: [...]` for batch execution

## When NOT to Use

- Task is inherently sequential (later steps depend on earlier output, not just a contract)
- Only 1–2 tasks total (overhead of subagent dispatch exceeds savings)
- Tasks modify the same file (conflict risk)
- User explicitly wants sequential execution

## Core Concepts

### Wave Structure

Tasks are grouped into **waves**. All tasks within a wave run concurrently. Waves execute sequentially — a later wave starts only after all tasks in the prior wave complete.

```
Wave 0 → Wave 1 (parallel) → Wave 2 → Wave 3
```

| Wave | Purpose | Subagents | Example |
|------|---------|-----------|---------|
| 0 | Foundation: shared config, types, contracts | 1 | `config.js` with all constants |
| 1 | Independent modules: each writes a different file | 2–6 (parallel) | `moduleA.js`, `moduleB.js`, ... |
| 2 | Integration: assemble modules into final artifact | 1 | `index.html` that imports all |
| 3+ | Verify, deploy | 1 | Browser check, Netlify deploy |

### Dependency Graph

Every parallel-optimized plan MUST include an ASCII dependency graph. This is the single source of truth for execution sequence:

```
WAVE 0 (1 subagent)
  T0: config/contract ──────────────────┐
                                        │
WAVE 1 (parallel — up to 6 subagents)   │
  ┌────────┐ ┌────────┐ ┌────────┐     │
  │ T1A    │ │ T1B    │ │ T1C    │ ◄───┘
  └───┬────┘ └───┬────┘ └───┬────┘
      └──────────┼──────────┘
                 ▼
WAVE 2 (1 subagent)
  T2: integrator
```

### Module API Contract

The **critical safety boundary** for parallel execution. Define this BEFORE dispatching Wave 1 subagents:

**Rules:**
1. Each Wave 1 subagent writes a **different file** — zero conflict risk
2. A **shared config module** (Wave 0) exports all constants/types
3. Each Wave 1 module exports a **single factory function** with documented signature
4. Modules receive dependencies as **parameters** (THREE namespace, scene object, etc.) — NOT via imports from sibling modules that don't exist yet
5. The integrator (Wave 2) imports all modules, calls each factory, and passes wired objects

**Contract format example:**
```
config.js       → exports CONSTANTS (all modules import from this)
moduleA.js      → export function createA(deps) → returns TypeA
moduleB.js      → export function createB(deps) → returns TypeB
integrator      → imports all modules, calls factories, wires results
```

### Task Decomposition Table

Include in every parallel plan:

| ID | Task | Priority | Wave | Deps | Parallel? |
|----|------|----------|------|------|-----------|
| T0 | Config/contract | P0 (critical) | 0 | — | No |
| T1A | Module A | P1 | 1 | T0 | Yes |
| T1B | Module B | P1 | 1 | T0 | Yes |
| T2 | Integrator | P0 (critical) | 2 | T0 + all T1x | No |
| T3 | Verify | P0 (critical) | 3 | T2 | No |

## Execution Steps

### Mandatory Preflight for Interactive 3D Tasks

Before dispatching implementation agents for a Three.js model, perform a coordinate-level gap analysis of the current geometry and composite transforms. Record the world-space anchor contract for every requested connection (for example: hub → crank → pedal, body → limb → control). Treat visual alignment as a first-class acceptance criterion, not a post-hoc polish step.

The plan must include, in this order:

1. Current-object and coordinate gap analysis.
2. Task/subtask/priority/dependency table.
3. ASCII dependency graph showing waves and gates.
4. One-file ownership for parallel agents.
5. Static/API integration gate before browser QA.
6. Screenshot-based visual verification of connected geometry from the default and at least one rotated view.
7. Production smoke test after deployment.

When a subagent's geometry output passes syntax but fails visual alignment, preserve the API contract and fix the coordinate/parenting implementation directly; do not declare completion from syntax or static checks alone.

### Orchestrator-Direct vs Subagent-Dispatched Tasks

Not every wave needs a subagent. A key optimization is deciding which tasks the **orchestrator does directly** vs which get dispatched:

| Task Type | Who Does It | Why |
|-----------|-------------|-----|
| Wave 0: Config files, directories, dependency install | **Orchestrator directly** | Fast (2-5 min), sequential, no reasoning needed — subagent overhead exceeds savings |
| Wave 1: Independent multi-file creation | **Subagents (parallel)** | This is where concurrency pays off — each writes a different file |
| Wave 2: Integration assembly | **Subagent** (if complex) or **orchestrator** (if trivial wiring) | Only dispatch if the integrator needs to reason about module wiring |
| Wave 3+: Verification (tests, syntax checks, smoke tests) | **Orchestrator directly** | Running commands and reading output is fast — no reason to pay subagent overhead |

**Rule of thumb:** If a task is 1-2 tool calls (write file, run command), the orchestrator should do it directly. Dispatch subagents only when the task involves 3+ steps of independent work.

### Step 1: Restructure the plan (if not already parallel)

If given a sequential plan, identify which tasks:
- Write different files → can be parallelized
- Share no mutable state → can be parallelized
- Can be assembled by a later integrator → can be parallelized

Extract shared constants into a Wave 0 config module. Define the module API contract.

### Step 2: Execute Wave 0 (foundation) — Orchestrator Direct

Create the shared config/contract module, directory structure, and install dependencies **yourself** (do not dispatch a subagent). This is typically 3-5 quick tool calls:

```
# Example: Python project foundation
write_file("pyproject.toml", ...)       # config
terminal("mkdir -p static/js tests")     # directories
terminal("uv sync --extra dev")          # dependency install
```

Verify it compiles before proceeding:

```bash
node --check js/config.js  # or language-appropriate check
```

### Step 3: Dispatch Wave 1 (parallel modules)

Use `delegate_task` with `tasks: [...]` to dispatch all Wave 1 subagents in a **single call**:

```
delegate_task(tasks: [
  { goal: "Create js/moduleA.js ...", context: "..." },
  { goal: "Create js/moduleB.js ...", context: "..." },
  { goal: "Create js/moduleC.js ...", context: "..." },
])
```

**Key:** Each subagent's `context` field must include:
- The import path to `config.js` and what it exports
- The exact factory function signature to export
- What parameters it receives (THREE namespace, scene, etc.)
- That all meshes/objects must be self-contained
- **Complete file contents when files are predetermined from the plan.** If the plan already specifies exact code, embed it verbatim in the context — the subagent should write it, not redesign it. Only let the subagent design code when the plan describes behavior but not implementation.

### Step 4: Execute Wave 2 (integration)

After all Wave 1 subagents complete, dispatch the integrator (or do it yourself if wiring is trivial). Its job:
1. Import all modules
2. Call each factory function with wired parameters
3. Set up the runtime (scene, camera, renderer, animation loop)
4. Verify all module syntax is valid before writing the integrator file

**Pitfall:** The integrator subagent must WAIT for all Wave 1 files to exist. If dispatching Wave 2 as a background subagent alongside Wave 1, instruct it to verify file existence first.

### Step 5: Verify (Wave 3) — Orchestrator Direct

Run verification yourself — do not dispatch a subagent for test runs or syntax checks:

```bash
uv run pytest tests/ -v          # or pytest, npm test, etc.
node --check static/js/*.js      # syntax validation
python -c "import ast; ast.parse(open('file.py').read())"  # Python syntax
```

For web apps, start the dev server in background, curl headers/endpoints, then kill:

```
terminal(background=true): uv run python scripts/dev_server.py
terminal(): curl -sI http://localhost:PORT | head -10  # verify COOP/COEP headers
terminal(): curl -s http://localhost:PORT | head -5    # verify HTML served
process(action=kill, session_id=...)                    # stop server
```

**Pitfall:** Do NOT use shell `&` backgrounding in terminal — Hermes rejects it. Use `terminal(background=true)` then run health checks in a separate foreground terminal call.

### Step 6: Deploy (Wave 4)

Deploy via appropriate tool (Netlify CLI, etc.).

## Dispatch Patterns

### Pattern 1: All-at-once (preferred when waves are well-separated)

Dispatch Wave 0, then Wave 1 (5 parallel), then Wave 2+ as separate `delegate_task` calls. Wait for each wave to complete before starting the next.

### Pattern 2: Cascading (when Wave 2 can be pre-dispatched)

Dispatch Wave 1 and Wave 2 together, with Wave 2's context explicitly stating "WAIT for these files to exist first." The Wave 2 subagent polls for file existence before proceeding.

```
delegate_task(tasks: [
  { goal: "Create module A ...", context: "..." },
  { goal: "Create module B ...", context: "..." },
  { goal: "Create integrator. WAIT for module A and B files to exist first, then verify exports match, then assemble.", context: "..." }
])
```

**Pitfall:** Cascading dispatch risks the integrator starting before modules are ready. Only use when the integrator's context is explicit about waiting.

## Performance Expectations

| Plan Type | Sequential Time | Parallel Time | Savings |
|-----------|----------------|---------------|---------|
| 5-module project | ~35 min | ~18 min | ~48% |
| 3-module project | ~20 min | ~12 min | ~40% |
| 2-module project | ~15 min | ~10 min | ~33% |

**Diminishing returns below 3 parallel tasks** — the overhead of subagent dispatch starts to approach the savings.

## Pitfalls

- **File conflicts:** Two subagents writing the same file. Fix: enforce one-file-per-subagent rule.
- **Contract drift:** A subagent exports `createFoo` but integrator imports `makeFoo`. Fix: the contract in the plan must specify exact export names, and the integrator must verify.
- **Premature integration:** Wave 2 starts before Wave 1 files exist. Fix: either wait for Wave 1 to complete, or instruct Wave 2 to poll for file existence.
- **Forced parallelism:** Splitting a monolithic task that can't actually be parallelized. Fix: if a task can't be decomposed into independent files, keep it sequential.
- **Subagent context starvation:** Subagent doesn't know the project structure or conventions. Fix: include the full module API contract, file paths, and import patterns in each subagent's `context` field.
- **Subagent writes overwrite parent patches:** When you dispatch async subagents that re-create the same fragment files the parent session has also patched, the async results arrive AFTER the parent fix and silently revert it. The assembled output loses the fix. Mitigations: (a) apply critical fixes to the CONCATENATED output in Wave 2, not to individual fragments, (b) bake alignment fixes into the subagent context FROM THE START so they're never overwritten, or (c) have the assembler re-apply fixes as a post-processing step.
- **THREE namespace pattern:** When modules need Three.js, pass `THREE` as a parameter rather than having each module import from CDN. Only the integrator imports from CDN. This avoids version drift and keeps modules testable.

## References

- `references/parallel-execution-planning.md` — Complete worked example: Three.js 3D chair viewer decomposed into 5 parallel modules + integrator, with wave diagrams, contract patterns, and full dispatch context text.
- `references/python-multilang-parallel.md` — Multi-language project patterns (Python tools + JS bridge + HTML UI + PyScript WASM): lane decomposition, language-specific verification, dev server smoke tests, uv-specific notes.
