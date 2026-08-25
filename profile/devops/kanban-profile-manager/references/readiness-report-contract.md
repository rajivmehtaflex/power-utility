# Readiness Report JSON Contract

The structured output produced by `scripts/profile_check.py`. Every field is
guaranteed present. Downstream consumers should treat unknown fields as
advisory only.

## Top-level structure

```json
{
  "phase": "profile-preparation",
  "execution_started": false,
  "mode": "provision-approved",
  "registry_path": "/absolute/path/to/registry.yaml",
  "generated_at": "2026-08-01T19:56:39Z",
  "existing_profiles": ["default", "researcher"],
  "results": [],
  "summary": {
    "all_ready": true,
    "total_roles": 3,
    "reused": 2,
    "created": 1,
    "blocked": 0,
    "failed": 0,
    "needs_update": 0
  }
}
```

## Per-role result object

```json
{
  "role": "excel-specialist",
  "profile_name": "excel-specialist",
  "action": "created",
  "profile_created": true,
  "ready_for_dispatch": true,
  "reason": "Profile created from approved template",
  "template": "default",
  "verification": {
    "exists": true,
    "description_ok": true,
    "skills_ok": true,
    "tools_ok": true
  }
}
```

## `action` field — all valid values

| Value | When | `ready_for_dispatch` | `profile_created` |
|---|---|---|---|
| `reused` | Profile exists and passes verification | `true` | `false` |
| `created` | Profile was provisioned and passes verification | `true` | `true` |
| `needs_update` | Profile exists but fails one or more checks | `false` | `false` |
| `blocked` | Policy forbids creation or role is unknown | `false` | `false` |
| `failed` | CLI command failed during create or verify | `false` | `false` |

## Phase 1 boundary enforcement

Two fields are **hard contracts** — they must never change regardless of
provisioning mode:

- `"execution_started": false` — the manager never creates Kanban tasks or
  starts workers.
- `"phase": "profile-preparation"` — marks the output as Phase 1 only.

If a downstream consumer sees `execution_started: true`, the output did not
come from the Phase 1 manager and should be rejected.
