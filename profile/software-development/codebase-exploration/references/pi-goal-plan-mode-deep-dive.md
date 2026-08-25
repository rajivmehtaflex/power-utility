# Pi `/goal` and `/plan` deep-dive reference

Session-derived reference for explaining Pi slash-command runtimes from source. Re-check the repository before relying on line numbers; the anchors below describe the `narumiruna/pi-extensions` layout inspected on 2026-08-13.

## CodeGraph evidence checklist

Before exploration, run `codegraph status -j`. Record:

- `initialized`, `projectPath`
- `fileCount`, `nodeCount`, `edgeCount`
- `pendingChanges`, `worktreeMismatch`
- `index.state`

For the inspected checkout, the healthy index reported CodeGraph `1.5.0`, 1,085 files, 21,932 nodes, 109,107 edges, `pendingChanges=0`, `worktreeMismatch=null`, and `state=complete`.

## `/goal` anchor map

| Concern | Source anchor |
|---|---|
| public entrypoint | `packages/pi-goal/src/index.ts` → `./goal.js` |
| composition root | `packages/pi-goal/src/goal.ts:13-28` |
| command parser | `packages/pi-goal/src/command.ts:95-196` |
| command registration | `packages/pi-goal/src/command-registration.ts:16-123` |
| command controller | `packages/pi-goal/src/commands.ts` |
| runtime/state owner | `packages/pi-goal/src/runtime.ts` (`GoalRuntime`) |
| lifecycle | `packages/pi-goal/src/lifecycle.ts:35+` |
| completion/block/wait tools | `packages/pi-goal/src/tools.ts:59+` |
| prompt construction | `packages/pi-goal/src/prompts.ts:27-115` |
| persistence | `packages/pi-goal/src/persistence.ts:18-136` |
| ordered queue | `packages/pi-goal/src/queue.ts:39-126` |
| Goal-tool visibility | `packages/pi-goal/src/tool-policy.ts:20-180` |
| settings | `packages/pi-goal/src/settings.ts:6-31` |
| managed sibling-run protocol | `packages/pi-goal/src/run-protocol.ts` |
| public behavior | `packages/pi-goal/README.md` |

Composition flow:

```text
goal()
  → GoalRuntime
  → GoalCommandController
  → GoalRunController.register
  → registerGoalTools
  → registerGoalCommand
  → registerGoalLifecycle
```

Core distinction: `/goal` is an autonomous execution supervisor, not a read-only mode. It owns an active goal, continuation intent, safety counters, persistence, terminal protocol tools, and optional ordered queue.

## `/goal` state and loop

Statuses:

```text
active | queued | paused | blocked | usage_limited | budget_limited | complete
```

`waiting` is metadata on an active goal, not a separate status.

Activation:

```text
parse objective/budget
  → validate and optionally confirm replacement
  → prepare Goal tools
  → create ActiveGoal with unique id
  → persist `goal-state`
  → send owned kickoff prompt
```

Automatic continuation (`GoalRuntime.requestContinuation` / `dispatchContinuationIfSettled`, around `runtime.ts:350-399`) is dispatched only when:

- the goal ID and active state still match;
- the goal is not waiting;
- required Goal tools are available;
- automatic-turn and no-progress limits have not fired;
- Pi is idle and has no pending messages.

It sends a marked follow-up with `deliverAs: "followUp"`. Owned prompt markers and generation/ID checks prevent stale, duplicate, replaced, or cancelled turns from reviving a goal.

Lifecycle boundaries to inspect: `session_start`, `session_shutdown`, `session_before_compact`, `session_compact`, `input`, `message_start`, `context`, `tool_call`, `tool_execution_end`, `before_agent_start`, `agent_start`, `turn_end`, `agent_end`, and settled/idle dispatch.

## Goal tools

- `goal_complete({ goal_id, summary })`: exact current-ID guard; rejects missing/stale IDs, inactive goals, empty/contradictory summaries; transitions to complete and schedules queue advancement.
- `goal_blocked({ goal_id, reason, evidence, repeated_turns })`: requires current ID, concrete evidence, and `repeated_turns >= 3`; transitions to blocked only for a true external/user impasse.
- `goal_wait({ goal_id, reason, resume_after_ms? })`: keeps the goal active but suppresses automatic continuation until external input, explicit resume, or an optional bounded wake deadline.

Prompt guidance is not the only safety mechanism. Verify the runtime's `tool_call` handler, active-tool policy, stale-call blocking, state transition, and ID guards independently.

## Persistence and queue details

Canonical persisted data:

```ts
{
  goal: ActiveGoal | null,
  queue?: ActiveGoal[],
  pendingAction?: PendingQueueAction
}
```

`loadGoalStateFromSession` reads the latest canonical `goal-state` custom entry, normalizes fields, and falls back to a legacy `goals-state` shape. Invalid state fails closed. Queue items have independent budgets, counters, elapsed time, IDs, and safety state. Completion/skip/priority transitions are persisted as pending actions and dispatched only from a settled boundary. If experimental queue state is restored while `experimental.goals` is disabled, the queue freezes (`queue off`) instead of continuing.

## `/plan` comparison anchors

Standalone Plan mode:

- entrypoint: `packages/pi-plan-mode/src/index.ts`
- runtime: `packages/pi-plan-mode/src/plan-mode.ts`
- command parser: `packages/pi-plan-mode/src/command.ts`
- state: `packages/pi-plan-mode/src/state.ts`
- tool policy: `packages/pi-plan-mode/src/tool-policy.ts`
- handoff/actions: `packages/pi-plan-mode/src/plan-action-controller.ts`

Integrated copies:

- `packages/pi-workflow/src/goal/`
- `packages/pi-workflow/src/plan/`
- composition: `packages/pi-workflow/src/workflow.ts:32-267`

Plan mode is approval-gated and read-only: active-tool replacement plus a `tool_call` enforcement hook block mutation. Goal mode preserves ordinary execution tools and supervises autonomous continuation. Do not describe `/goal` as Plan mode with a different prompt.

The integrated workflow wires:

```text
Goal canStartGoal ↔ Plan active/implementation guard
Plan canStartPlan ↔ active Goal guard
Plan implementation → goalHandle.commands.startGoal(...)
Goal state sink → planHandle.handleGoalState(...)
```

It links the Plan implementation ID to the actual Goal ID and relinks on nonterminal ID rotation. Compare persisted `plan-mode-state` and `goal-state` entry indexes during restore to resolve conflicts. Standalone `pi-goal`/`pi-plan-mode` and integrated `pi-workflow` each register overlapping command surfaces; enabling both sets can cause duplicate `/goal` and `/plan` registration.

## Explanation output shape

A source-grounded answer should contain:

1. CodeGraph freshness and scope.
2. Entry/composition path.
3. Exact command table and feature flags.
4. State/status model.
5. Lifecycle and settled-boundary loop.
6. Tool contracts and actual enforcement points.
7. Persistence/restart/legacy normalization.
8. Plan comparison and integrated handoff.
9. Duplicate-registration and untested-status caveats.

Do not claim tests passed unless they were actually run; distinguish inspected test coverage from execution results.
