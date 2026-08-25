---
name: codebase-exploration
description: "Explore codebases with CodeGraph: symbols, calls, impact."
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: codebase-inspection, spike, systematic-debugging, project-feature-maintenance
  hermes_tags: codegraph, code-intelligence, code-navigation, symbol-analysis, call-graph, impact-analysis, code-exploration
  platforms: linux, macos, windows
  prerequisites_commands: codegraph
  version: 1.0.0
---

# Codebase Exploration with CodeGraph

Understand any codebase — symbols, call graphs, architecture, and change impact — using [CodeGraph](https://github.com/getcodegraph/codegraph).

## When to Use

- **"How does X work?"** — explore a function, class, or module's architecture
- **"What calls this?" / "What does this call?"** — caller/callee traces
- **"What breaks if I change Y?"** — impact analysis before editing
- **"Where is Z defined / used?"** — symbol lookup across the codebase
- **"What files are in this project?"** — project structure from the index
- **"Which tests cover changed files?"** — affected test discovery

Use this **before** editing unfamiliar code — it's more accurate than grep/search/Read loops and produces far fewer tokens.

## Prerequisites

```bash
# Install CodeGraph (macOS)
brew install codegraph

# Verify
codegraph --version
```

## Step 1 — Initialize a Project

```bash
cd /path/to/your/project
codegraph init
```

This creates a `.codegraph/` directory and builds an index of all code files (Python, JS, TS, Kotlin, Go, Rust, Java, YAML, etc.). Markdown and binary files are skipped.

Options:
- `-f, --force` — use if the path is near your home directory (safety guard)
- `-v, --verbose` — detailed worker lifecycle output

## Step 2 — Keep the Index Fresh

```bash
# Fast incremental sync (use after editing)
codegraph sync

# Full rebuild (rare — after major refactors)
codegraph index
```

Use `sync` as part of your daily workflow. It re-parses only changed files (sub-second).

## CLI Query Commands

### Natural Language Exploration

```bash
codegraph explore "how does user authentication work"
codegraph explore "AuthService loginUser session-manager"
codegraph explore -p ~/other-project "vector processing"
```

Returns verbatim source of relevant symbols grouped by file, plus call paths. Same output as the MCP tool.

### Symbol Search

```bash
codegraph query "getUser"           # find symbol everywhere
codegraph query "class Payment*"    # pattern matching
```

### Single Symbol Deep-Dive

```bash
codegraph node "getUser"            # symbol source + caller/callee trail
codegraph node "src/auth.ts"        # read file with line numbers + dependents
```

### Call Graph

```bash
codegraph callers "validate_token"    # who calls this function
codegraph callees "process_order"     # what does this function call
```

### Impact Analysis

```bash
codegraph impact "getUser"            # what code is affected by changing this symbol
```

Shows blast radius: callers up the stack, dependents, and whether covering tests exist.

### Affected Tests

```bash
# Find test files affected by source changes
codegraph affected src/auth.ts src/payments.ts
```

Useful before running CI to know exactly which test suites to execute.

### Project Structure & Status

```bash
codegraph files    # file tree from the index
codegraph status   # index stats (files, symbols, edges, languages)
codegraph status -j  # JSON output for scripting
```

## MCP Integration (Hermes Agent)

CodeGraph is already configured as an MCP server in Hermes. The tool `codegraph_explore` is available and I use it automatically when you ask code questions. No manual setup needed after `codegraph init`.

Config in `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  codegraph:
    command: codegraph
    args:
      - serve
      - --mcp
    timeout: 120
    connect_timeout: 60
    enabled: true
```

## Source-grounded visual explainers

When the user asks to understand an execution-heavy codebase through HTML/CSS/JavaScript, animation, diagrams, or an implementation plan, use CodeGraph as the source-of-truth backbone:

1. Confirm index freshness with `codegraph status -j`; inspect `pendingChanges`, `worktreeMismatch`, and the indexed file count before describing coverage.
2. Explore the complete runtime path, not only the central class: UI/event entry point → boundary/bridge → worker or async runtime → orchestrator loop → tools/services → completion/error rendering.
3. For CLI or library repositories, replace the browser-specific path with the actual host surface: REPL/input loop → composition root/builder → config/provider adapter → context/session → core loop → tool registry/function → observation/final off-ramp → history/memory → printed/API result. Never invent browser, worker, or bridge layers absent from source.
4. When the target consumes an editable sibling dependency, inspect the sibling's actual loop/session/registry implementation at the boundary, and show raw concrete-object crossings when adapters bypass a Protocol seam. Keep the explainer separate from both runtimes.
5. Cross-check CodeGraph output against the current on-disk entry points, tests, and project instructions. Older design docs or playbooks may describe an earlier architecture and must not override current source.
6. Build a compact flow table before authoring: every visible node and edge gets a checked file/symbol/line anchor, while lane names that are only presentation groupings are labeled as such.
7. Use deterministic evals/scripted clients as the source for representative payloads and error traces when available. Time-dependent or provider-dependent tools should use the test fixture's deterministic output and be labeled illustrative, not live.
8. Build static checks around the repository's actual test convention (`evals/deterministic/` as well as `tests/`), and keep artifact checks non-importing when editable dependencies or provider SDKs can contaminate collection.
9. Prefer a deterministic replay for a standalone explainer unless the user explicitly asks for live instrumentation. Label it as a replay; do not imply that the HTML artifact executes the real model, worker, or tools.
10. For an interactive explainer, synchronize one step data model with the SVG highlights, timeline, inspector, and source detail. Set a default active step and keep the narrative in HTML so JavaScript failure or disabled JavaScript does not blank the page.
11. Plan static checks for required source anchors/message labels and browser verification for SVG geometry, animation controls, responsive layout, console errors, keyboard operation, and reduced-motion behavior.
12. If an isolated ad-hoc verifier is required, create it with an OS-safe `hermes-verify-` tempfile, use absolute executable paths when the isolated PATH omits user-managed tools, clean Python/JavaScript temp files in `finally`, and report it as ad-hoc verification rather than canonical suite status.

See `references/source-grounded-visual-explainers.md` for the reusable data model, execution-path checklist, and verification recipe. See `references/cli-harness-replay.md` for CLI/library source modeling, deterministic traces, and isolated ad-hoc verification.

## Agent-mode and Pi extension planning

When the requested feature changes agent phases, tool access, lifecycle behavior, or implementation handoff, use the source-grounded workflow in `references/pi-extension-plan-mode-architecture.md`. Trace the complete extension path with CodeGraph before writing the plan; separate pure state, policy, prompt, Pi lifecycle boundaries, and handoff; recommend an isolated sibling package when a stable extension already owns the same slash command; and stage the MVP before adding Bash, persistence, UI, settings, or fresh-session behavior.

## Slash-command and lifecycle deep dives

When the user asks how a Pi slash command works (for example, `/goal`, `/plan`, or a workflow command), treat it as a runtime-architecture investigation rather than a symbol lookup:

1. Verify CodeGraph freshness first and record `initialized`, `projectPath`, `fileCount`, `nodeCount`, `edgeCount`, `pendingChanges`, `worktreeMismatch`, and `index.state`.
2. Locate every registration surface: the standalone package, its `src/index.ts` re-export, composition root, root `package.json` `pi.extensions` entry, and any integrated sibling package that may register the same command.
3. Trace the complete path with focused CodeGraph queries: composition root → command parser/registration → controller → runtime/state → lifecycle hooks → tools → persistence → UI/status or continuation.
4. Inspect the command parser and public README together. Report exact routes, aliases, feature flags, and behavior when an experimental feature is disabled; do not infer command semantics from names alone.
5. Separate prompt guidance from enforcement. For each safety claim, identify the actual `tool_call`, active-tool, event-bus, state-transition, or stale-request guard that enforces it.
6. Inspect `session_start`, `session_shutdown`, agent/turn/tool boundaries, compaction/retry handling, and settled/idle dispatch. Dynamic event-bus or reflection edges are runtime boundaries; follow them with narrower symbol queries instead of presenting the static graph as complete.
7. Inspect persistence and restart normalization, including canonical and legacy entry shapes, malformed-state behavior, queue/pending-action recovery, and whether state is session-owned or global.
8. Inspect tests and manifests, but do not execute the repository by default. Report test coverage that is present and say explicitly when pass/fail status was not run.
9. Compare related commands by responsibility. In particular, distinguish approval-gated read-only Plan mode from autonomous Goal execution; do not reuse one mode's tool policy or lifecycle assumptions for the other.
10. If an integrated workflow contains copied Plan/Goal modules, explain the bridge and warn about duplicate command/tool registration when standalone and integrated packages are enabled together.

A good explanation should include: entrypoints, command table, state machine, lifecycle sequence, tool contracts, persistence model, safety boundaries, continuation/handoff behavior, integration conflicts, and exact file/symbol/line anchors. Keep repository-specific evidence in a `references/` file rather than expanding the class-level procedure with one-session implementation detail. See `references/pi-goal-plan-mode-deep-dive.md` for the reusable comparison checklist and source-anchor model.

## Pitfalls

1. **Must run `codegraph init` per project** — no default index. Run it once after cloning/creating a project.
2. **Code files only** — CodeGraph indexes `.py`, `.js`, `.ts`, `.kt`, `.java`, `.go`, `.rs`, `.yaml`, etc. Markdown (`.md`), images, PDFs, and binary files are skipped. For content search in those, use `search_files()` instead.
3. **Sync before querying after edits** — `codegraph sync` is fast (sub-second) but the index is stale until you run it. The MCP server serves from the last indexed state.
4. **Large repos** — indexing time scales with file count. For very large monorepos, consider initializing CodeGraph at the sub-project level rather than the monorepo root.
5. **CodeGraph must be installed** — `brew install codegraph` on macOS. The MCP server won't start without it.
6. **No hot-reload on MCP server** — if you add a new MCP server to config.yaml, restart Hermes. The MCP client discovers servers at startup only.

## Reference Files

- `references/gdrive-operations-sequence.mmd` — Mermaid sequence diagram showing Google Drive operations flow discovered via CodeGraph exploration (4 pipeline flows: full ingestion, GDrive-only, finish, Xero-direct; plus mount/unmount operations and normalization details)
- `references/pi-mcp-adapter-integration.md` — CodeGraph-verified Pi extension integration (package.json pi block, cli.js config discovery, installMcpAdapter→initializeMcp→ServerManager call path, direct vs proxy surfaces, Mermaid recipe, puppeteer browser install fix)
- `references/macos-hermes-venv.md` — macOS Hermes Python venv isolation fix (`dataclass slots` / `No module named pip`) via `uv venv` with clean env; applies to any `python -m venv` work inside Hermes on Apple Silicon
