# Dynamic Orchestrator Agent Skill Publication Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` or `superpowers:subagent-driven-development` to implement this plan task-by-task.

**Goal:** Add the `dynamic-orchestrator` skill to `rajivmehtaflex/power-utility` as a portable Agent Skills package that can be installed into Codex and other compatible agents.

**Architecture:** Add the skill under the existing `profile/autonomous-ai-agents` collection, preserving the repository’s normalized mono-repo structure. Use `npx skills` for discovery and installation, and update the repository’s manifest, README index, and validation report.

**Tech Stack:** Markdown, YAML frontmatter, JSON, Git, `npx skills`, `skills-ref`.

**Spec:** [Agent Skills specification](https://agentskills.io/specification)

## Global Constraints

- `SKILL.md` must remain valid Agent Skills format.
- `name: dynamic-orchestrator` must match its parent directory exactly.
- The description must explain both what the skill does and when to use it.
- Keep the existing `subagent-orchestration` skill unchanged.
- Do not add machine-specific secrets or credentials.
- The skill must report when the target runtime lacks real subagent controls.
- The repository is a multi-skill mono-repo, so retain `power-utility` as the repository name.
- Follow the repository’s existing `README.md`, `MANIFEST.json`, and `VALIDATION_REPORT.md` conventions.

### Task 1: Add the portable skill package

- Create `profile/autonomous-ai-agents/dynamic-orchestrator/SKILL.md`.
- Preserve the supplied dynamic-orchestrator instructions.
- Use spec-compatible `name`, `description`, `compatibility`, and `metadata.version` fields.
- Keep the body runtime-neutral; do not add Hermes-only tool names.

### Task 2: Update repository discovery and installation documentation

- Add `dynamic-orchestrator` to the README index under `profile / autonomous-ai-agents`.
- Update the total count to the post-change manifest count.
- Document this Codex installation command:

```bash
npx skills add rajivmehtaflex/power-utility \
  --skill dynamic-orchestrator \
  --agent codex \
  --global \
  --copy \
  -y
```

### Task 3: Synchronize repository metadata

- Add the new skill to `MANIFEST.json` using the repository-relative normalized path.
- Mark it `spec_compliant: true` with an empty warnings list.
- Update `VALIDATION_REPORT.md` to reflect 72 total skills, 72 compliant skills, and zero failures.
- Do not modify unrelated entries.

### Task 4: Validate and verify remote installation

Run:

```bash
npx -y skills-ref validate profile/autonomous-ai-agents/dynamic-orchestrator
npx skills add rajivmehtaflex/power-utility --list
npx skills add rajivmehtaflex/power-utility \
  --skill dynamic-orchestrator \
  --agent codex \
  --global \
  --copy \
  -y
```

Confirm that the skill is discoverable, installs for Codex, and can be invoked in a new session with `$dynamic-orchestrator`.

### Task 5: Commit and publish

- Review the final diff for only the requested skill, documentation, metadata, validation report, and plan file.
- Commit with `feat: publish dynamic-orchestrator agent skill`.
- Push the feature branch or open a pull request according to repository permissions.
- Re-run discovery and installation checks against the pushed repository.

## Acceptance Criteria

- The new skill exists at `profile/autonomous-ai-agents/dynamic-orchestrator/SKILL.md`.
- `skills-ref validate` passes.
- `npx skills add ... --list` discovers the skill.
- Codex-targeted installation succeeds.
- README, manifest, validation report, and this plan are synchronized.
- Existing orchestration skills remain unchanged.
