---
name: dynamic-orchestrator
description: Coordinate substantive implementation work with real subagents using adaptive assignments, lead-mediated handoffs, review, and verified reporting. Use when a task needs delegated implementation, adaptive ownership, agent handoffs, independent review, or correction loops.
compatibility: Requires an agent runtime with real subagent spawning, result retrieval, follow-up, and lifecycle controls; otherwise report that delegated workflow is unavailable and use only an explicitly authorized lead-only path.
metadata:
  version: "1.0.0"
---

# Dynamic Orchestrator

Use this skill only when the user explicitly invokes it. It coordinates work; it does not replace the user's goal, acceptance criteria, limits, or permissions.

## Lead responsibilities

The main agent is the lead. It owns the interpretation of the request, selects roles and assignments dynamically, keeps the critical path moving, routes communication, inspects artifacts, integrates changes, and gives the final evidence-backed report.

Start by extracting the current goal, acceptance criteria, editable artifacts, limits, and allowed side effects. Do not create agents for a trivial task or for work that has no useful independent boundary. Before delegating, decide what the lead can do immediately without waiting; do not delegate an urgent blocking step when local progress is available.

## Capability and scope checks

Inspect the actual tool list before promising delegation. Use real subagent controls for spawning, receiving results, follow-up, and lifecycle management when those controls exist. Never simulate separate agents through role-playing or by writing invented agent messages.

If the request requires delegation and the real capability is missing or a required delegation call fails, report the missing or failed capability and stop the delegated workflow. If delegation is optional, continue only with a user-authorized local path and say that no real delegation occurred. Prompt instructions guide behavior; they do not hard-enforce concurrency, ownership, permissions, or tool success, so the lead must verify those conditions from tool state and artifacts.

Respect the user's scope and existing permissions. Do not infer authorization for unrelated files, external systems, messages, or irreversible actions. If a necessary step needs new authority, pause and ask the user.

## Assignment and ownership

Choose roles from the actual work, such as test author, implementation owner, documentation owner, investigator, or reviewer. The team is not fixed: continue, resume, replace, or create agents based on current evidence and the newest requirement. Reuse completed work when it remains valid, and tell the user when an assignment changes.

Maintain an ownership map. Each editable file or other mutable artifact has at most one active writer at a time. A reviewer is read-only unless it receives a separately assigned correction task. Give each agent a narrow scope, the required context, the expected output, and an explicit list of files it may edit. Keep the default at no more than three concurrently active subagents, or the lower limit specified by the user. Close or otherwise release finished agents when the available lifecycle supports it.

## Parallel work and dependencies

Dispatch independent assignments in parallel when they do not share mutable state or depend on one another's unfinished output. Sequence work when a result is a prerequisite, when agents would edit the same artifact, or when a single investigation needs shared context. Keep tests, documentation, implementation, and logs in disjoint write scopes whenever possible.

Use a meaningful acceptance check before implementation when the project workflow supports it. For behavior changes, prefer a test-first red-green cycle and preserve existing useful coverage. Never remove or weaken a test merely to make a result pass.

## Evidence and handoffs

All relevant findings, decisions, and questions travel through the lead. An agent reports to the lead; the lead decides what is reliable, inspects the actual files or command output, and then sends a concise, explicit handoff to the next agent. Do not treat an agent's claim as verification.

When handing work off, include:

- the source and recipient agent identifiers;
- the concrete finding, requirement, or question being transferred;
- the affected artifact or decision; and
- the action the recipient should take and later report.

For a changed requirement or new finding, reassess the whole assignment map. Pass the updated criteria to every affected owner, preserve unaffected useful work, and avoid leaving an agent working from a stale contract.

## Review and correction

For substantive implementation work, use a separate reviewer from the implementer. Give the reviewer the current artifacts and acceptance criteria, and ask it to inspect real files and run focused checks plus the relevant suite. Keep the reviewer read-only by default.

When a reviewer reports a finding, the lead must determine whether it is genuine from the evidence. Send genuine findings back through the lead to the appropriate owner, correct them without changing the acceptance criteria, and rerun the relevant checks. Track correction rounds per issue. After two unsuccessful correction rounds for the same issue, report the blocker and the remaining evidence instead of hiding the failure or inventing success. If the review finds no genuine issue, record that outcome and do not manufacture a correction.

## Coordination records

Keep a concise coordination record when the user requests one or the task explicitly requires it. Use the user-specified location and format; otherwise report the record inline instead of creating an extra artifact. Record actual agent identifiers, role and file ownership, assignment order or parallelism, handoff summaries, actions taken after handoffs, review findings and correction counts, verification commands and results, and unresolved issues. Mark agent-reported results separately from lead-run verification, and never invent an identifier, finding, command result, or completion state.

## Final verification

Before reporting the work as complete, reread the acceptance criteria, inspect the final artifacts and ownership boundaries, and run the required verification commands freshly from the lead. Report the exact outcome, including failures or limitations. State unresolved issues plainly. A passing agent report, a clean-looking diff, or a plausible implementation is not a substitute for lead verification.
