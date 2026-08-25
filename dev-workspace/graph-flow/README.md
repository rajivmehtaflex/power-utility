# Graph Flow

[![skills.sh](https://skills.sh/b/rajivmehtaflex/graph-flow)](https://skills.sh/rajivmehtaflex/graph-flow)

Graph Flow is a portable Agent Skill for coordinating repository work as a durable, stateful graph. It is useful when work needs parallel units, conditional routing, independent verification, bounded repair loops, restart recovery, or an explicit human approval gate.

The skill is intentionally a control plane, not an agent framework. Its standard-library Python helper validates transitions and persists state; the host coordinator supplies agent dispatch, task handles, waiting, and result collection.

## Install

Install from GitHub with the Skills CLI:

```bash
npx skills add rajivmehtaflex/graph-flow
```

The equivalent full URL is:

```bash
npx skills add https://github.com/rajivmehtaflex/graph-flow
```

List the skill before installing:

```bash
npx skills add rajivmehtaflex/graph-flow --list
```

Install globally for a specific agent, such as Codex:

```bash
npx skills add rajivmehtaflex/graph-flow --skill graph-flow --agent codex --global
```

The default installation is project-scoped. Add `--copy` if symlinks are not suitable for your environment, or `--yes` for a non-interactive install.

## When To Use It

Use Graph Flow when a repository task has one or more of these characteristics:

- Independent work can run concurrently.
- Runtime inspection determines which implementation branch should run.
- A verifier must route evidence back to a repair worker.
- A risky action needs explicit human approval.
- The coordinator may restart and must resume from durable state.

For a small, linear edit, use the host agent's ordinary workflow instead.

## Quick Start

After installation, give your coding agent the goal. Graph Flow turns that goal into a reviewed plan; you do not need to hand-author a graph first.

1. Start a durable, graphless intake with the goal only:

```bash
python3 scripts/graph_state.py start \
  --repo <project-root> \
  --run-id <run-id> \
  --request '{"goal":"Add CSV export to the user profile page."}'
```

2. The coordinator inspects the repository and asks only for missing, decision-relevant information. It records each adaptive preflight or worker question with `request`; for example, this `single_select` request declares its accepted answers before you respond:

```bash
python3 scripts/graph_state.py request \
  --repo <project-root> \
  --run-id <run-id> \
  --request '{"kind":"input","answer_type":"single_select","prompt":"Which export formats belong in the first release?","rationale":"The implementation scope depends on this choice.","options":["CSV only","CSV and JSON"]}'

python3 scripts/graph_state.py respond \
  --repo <project-root> \
  --run-id <run-id> \
  --request-id request-1 \
  --answer '"CSV only"'
```

3. The coordinator generates requirements plus workstreams and nodes, including ownership paths, acceptance criteria, verification commands, dependencies, and approval boundaries. It persists that generated plan and opens the graph approval gate. In the optional Prime/Pi cockpit, the Action Center shows **graph approval** and the complete public plan projection. In headless use, inspect `status --format json` before approving: it contains requirements, `pending_approval`, workstreams, nodes (including resources and prompts), limits, and recent events. `status --format text` is summary-only and is not sufficient for graph approval.

```bash
python3 scripts/graph_state.py plan \
  --repo <project-root> \
  --run-id <run-id> \
  --definition '<generated-planned-graph-json>' \
  --requirements '<generated-requirements-json>'

python3 scripts/graph_state.py approve \
  --repo <project-root> \
  --run-id <run-id>
```

4. Repeatedly call `tick`. It yields the next deterministic action and generated node envelopes. The coordinator turns each executable envelope into the host-specific worker prompt described in `references/worker-envelope.md`, dispatches only those workers, records their allowed result with `complete`, then calls `tick` again. A ready human node is always shown for approval before executable work is dispatched alongside it.

5. Use the cockpit and lifecycle controls throughout the run:

```bash
python3 scripts/graph_state.py status --repo <project-root> --run-id <run-id> --format json
python3 scripts/graph_state.py status --repo <project-root> --run-id <run-id> --format text
python3 scripts/graph_state.py pause --repo <project-root> --run-id <run-id>
python3 scripts/graph_state.py resume --repo <project-root> --run-id <run-id>
python3 scripts/graph_state.py reconcile --repo <project-root> --run-id <run-id>
```

`pause` stops new dispatch and drains existing handles; `resume` is valid once the run is paused. `status --format json` is the complete, stable cockpit and approval projection; `status --format text` is a compact operational summary only. The coordinator, not an individual worker, owns the state file and decides what runs next.

## Example Prompt

Paste a goal-only request like this into your coding agent after installing the skill:

```text
Use the graph-flow skill to add user-profile export to this repository.
```

For a more detailed research/export request:

```text
Use the graph-flow skill to research India news from the last 24 hours,
collect date/title/description/url into a table, configure only approved
local tools, export a PDF in the current folder, and clean up temporary
artifacts. Inspect the environment, define acceptance criteria and resource
ownership, create independent work where safe, require approval before any
system or production-facing change, and verify the final PDF.
```

The coordinator first inspects the repository, then asks adaptive questions only when the goal leaves an important choice unresolved. It proposes generated workstreams and nodes for you to review, requests graph approval before dispatch, and emits bounded worker prompts with their owned paths and verification commands. It reports status, approval decisions, evidence, changed files, and remaining risks; after interruption it uses `reconcile` rather than replaying chat history.

For a smaller task, the same goal-only shape works. Add constraints only when they materially change scope, risk, or acceptance criteria.

## Graph Features

- Static `depends_on` prerequisites and `depends_on_any` alternatives.
- Runtime `transitions` for conditional branches and repair loops.
- Exclusive logical resource keys to prevent conflicting work.
- Goal-first intake with typed adaptive preflight and runtime input requests.
- Generated, revisioned workstreams and planned nodes that require graph approval before dispatch.
- Generated immutable worker envelopes with precise ownership, input results, feedback, and allowed outcomes.
- Per-node attempt limits and a global transition circuit breaker.
- Durable task registration, claims, attachment, completion, and reconciliation.
- Human approval nodes and failure outcomes that block safely.
- `status` cockpit output plus pause/drain/resume controls and atomic state updates shared by Git worktrees.

## Runtime Adapter Capabilities

Adapters translate the same immutable worker envelope and reducer controls to their host; they do not let workers select graph transitions or mutate graph state. The offline fixtures in `tests/fixtures/` pin this portable contract without calling any host harness.

| Adapter | Executable mapping | Capability tier | Headless fallback |
| --- | --- | --- | --- |
| Codex | Explorer, worker, or default threads, by planned role | Full when persisted task IDs are inspectable; otherwise Managed | Complete `status --format json` plus typed request/approval and result JSON; text is summary-only |
| Prime Agent | One `rlm()` invocation per executable envelope | Full when run IDs are inspectable; otherwise Managed | Complete reducer JSON input/output contract; text is summary-only |
| Pi core | One sequential invocation in the active process | Sequential | `status --format json` for approval, standard input/output JSON; text is summary-only |
| pi-subagents | One async subagent run per executable envelope | Full when run IDs are inspectable/resumable; otherwise Managed | Complete reducer JSON projection, request/approval input, and result envelopes; text is summary-only |

Every executable adapter persists a native handle through `register`, or `claim` followed by `attach`, then uses that exact handle for `inspect`, `wait`, steering delivery, `stop`, and `complete`. A host that cannot safely inspect a handle after restart blocks the graph with that handle and cause instead of redispatching uncertain work. See `references/runtime-adapters.md` for the host mappings and `references/driver-contract.md` for the tier guarantees.

## Optional Prime/Pi Cockpit Package

The skill and Python reducer work without a host package. The optional cockpit package adds the Pi-compatible widget, Action Center, dialogs, and slash command; its `package.json` already declares the extension through the `pi` manifest.

For a local Pi activation, install this checked-out package globally or for the current project, then enable its resources in Pi configuration if they have been disabled:

```bash
pi install -l /absolute/path/to/graph-flow
pi config -l
```

Prime Agent hosts that support the shared Prime/Pi package API can load the same package through their configured local package source and activate its declared extension. Graph Flow does not bundle a separate Prime-specific installer. Review and trust the local package before activation because extensions run with the host user's permissions.

In an activated Prime/Pi cockpit, use:

```text
/graph-flow <run-id> [status|answer|approve|pause|resume|steer|stop|confirm-stop]
```

`steer` requires a node ID and message. `confirm-stop` takes the terminal-handle evidence JSON required by `stop-confirm`. `answer` opens a pending typed request (or pending approval); `approve` opens a pending approval directly. Codex uses its native panel when available and the reducer's text/JSON controls otherwise. Pi core needs no cockpit package: it is the sequential fallback, running one executable envelope at a time in the active process.

## Approval and Controls

- `plan` creates or revises the generated graph; a no-node `approve` is the explicit approval for that graph and is valid only before dispatch.
- Review graph approval only through the complete `status --format json` projection (or a native Action Center). It includes requirements, `pending_approval`, workstreams, nodes/resources/prompts, effective limits, and recent events; the text format cannot substitute for it.
- When `tick` returns a ready runtime human node, it returns only that human envelope before any co-ready executable node. Record the decision with `approve --node <id> --result <file>`; no-node approval cannot bypass this gate.
- Typed preflight or runtime questions are persisted by `request`; use `respond --request-id <id> --answer <typed-json>` for the one open request.
- `pause` enters `pause_requested` and prevents new work. Repeated `tick` calls drain active handles to `paused`; only then can `resume` return the run to `running`.
- `stop-request` snapshots the active handles. Call `stop-confirm` only with terminal evidence for every snapshot handle; incomplete evidence keeps the run safely in `stop_requested`.

## Repository Layout

```text
SKILL.md                         Main agent instructions
scripts/graph_state.py           Deterministic state engine CLI
references/state-schema.md       Definition and envelope schema
references/driver-contract.md    Coordinator and worker contract
references/runtime-adapters.md  Host-specific adapter guidance
tests/test_graph_state.py        Black-box CLI test suite
tests/fixtures/*.json            Offline adapter-contract fixtures
```

## Development

The helper has no third-party runtime dependencies. Run the test suite with:

```bash
python3 -m unittest discover -s tests -v
```

The tests cover approval, conditional routing, bounded repair loops, verification evidence, stale handles, durable claims, resource validation, and restart-related state behavior.

## Safety And Limitations

Review a skill's source before installing it, especially when installing from an unfamiliar repository. Graph Flow does not make model calls, call vendor APIs, dispatch tasks, change worktrees, or make natural-language decisions. A host-specific coordinator must implement those capabilities and must not claim stronger restart guarantees than its task-handle support provides.

## References

- [Skills CLI documentation](https://www.skills.sh/docs/cli)
- [Skills CLI source and supported source formats](https://github.com/vercel-labs/skills)
- [Agent Skills specification](https://agentskills.io/specification)
- [Graph Flow skill instructions](SKILL.md)
