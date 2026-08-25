# Profile Provisioning Registry and Decision Contract

This reference is a starter registry for a Kanban profile-manager workflow. Keep it under version control or in the profile-manager's approved configuration area; do not infer provisioning policy from arbitrary task text.

## Example registry

```yaml
mode: reuse-only  # reuse-only | provision-approved | approval-required
max_auto_created_profiles: 8
profiles:
  orchestrator:
    description: Routes tasks, manages dependencies, and does not execute specialist work.
    capabilities: "Task decomposition, dependency graph construction, Kanban routing, work assignment, progress monitoring."
    existing_only: true
    required_toolsets: [kanban]

  data-analyst:
    description: Analyzes structured financial and marketplace data.
    capabilities: "Statistical analysis, trend identification, data visualization, financial modeling, marketplace analytics (Amazon, TikTok Shop, TEMU, B&Q)."
    base_profile: default
    skills: [data-analysis]
    allowed_providers: [openai, openrouter, nous]
    auto_create: false

  excel-specialist:
    description: Creates, edits, validates, and exports Excel workbooks.
    capabilities: "Excel workbook creation, formula validation, multi-sheet reporting, formatting, chart generation, CSV import/export."
    base_profile: default
    skills: [xlsx, document-generation]
    required_toolsets: [file, terminal]
    auto_create: false

  reviewer:
    description: Reviews outputs against acceptance criteria and reports defects.
    capabilities: "Quality assurance, output validation, defect reporting, acceptance criteria checking, compliance review, data accuracy verification."
    base_profile: default
    skills: [requesting-code-review]
    auto_create: false
```

The names and skills above are examples. Verify that each referenced skill, provider, and toolset exists on the target installation before using the registry.

## Decision contract

```json
{
  "requested_role": "excel-specialist",
  "canonical_role": "excel-specialist",
  "profile": "excel-specialist",
  "action": "reused",
  "profile_created": false,
  "template": null,
  "ready_for_dispatch": true,
  "reason": "Profile exists and satisfies the role contract",
  "verification": {
    "exists": true,
    "description_ok": true,
    "skills_ok": true,
    "tools_ok": true,
    "credential_policy_ok": true
  }
}
```

## Missing-role outcomes

### Reuse-only

```json
{
  "action": "blocked",
  "ready_for_dispatch": false,
  "reason": "No existing approved profile matches the requested role",
  "next_step": "Choose an existing profile or approve creation of a registered role"
}
```

### Provision-approved

```json
{
  "action": "created",
  "profile": "excel-specialist",
  "template": "default",
  "profile_created": true,
  "ready_for_dispatch": true
}
```

### Approval-required

```json
{
  "action": "blocked",
  "ready_for_dispatch": false,
  "proposed_profile": "new-role",
  "template": null,
  "reason": "The role is not registered; human approval is required"
}
```

## Operational rules

1. Use one canonical profile name per role.
2. Re-check profile existence immediately before creation.
3. Treat an already-created profile found during a race as a reusable success, then validate it.
4. Do not copy `.env`, OAuth tokens, or broad session state by default.
5. Do not create numbered duplicates such as `excel-specialist-2` without explicit authorization.
6. Keep profile creation separate from task execution; the newly created profile should not be assumed to be ready until it has been re-read and verified.
7. Store the decision in a Kanban comment, event, or structured handoff so the operator can audit why a card was reused, created, or blocked.

## Phase 1 readiness report (v2.0.0)

The `scripts/profile_check.py` script produces a structured report that
matches the contract in `readiness-report-contract.md`. Example for a
provision-approved run where `reviewer` was missing:

```json
{
  "phase": "profile-preparation",
  "execution_started": false,
  "mode": "provision-approved",
  "results": [
    {"role": "orchestrator", "action": "reused", "ready_for_dispatch": true},
    {"role": "data-analyst", "action": "reused", "ready_for_dispatch": true},
    {"role": "excel-specialist", "action": "reused", "ready_for_dispatch": true},
    {"role": "reviewer", "action": "created", "profile_created": true, "ready_for_dispatch": true}
  ],
  "summary": {
    "all_ready": true,
    "total_roles": 4,
    "reused": 3,
    "created": 1,
    "blocked": 0,
    "failed": 0,
    "needs_update": 0
  }
}
```

The `execution_started: false` and `phase: "profile-preparation"` fields are
hard contracts — they prove this output came from Phase 1 only.
