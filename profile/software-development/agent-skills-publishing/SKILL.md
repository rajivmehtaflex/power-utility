---
name: agent-skills-publishing
description: Use when adapting or publishing a Hermes skill for the cross-agent Agent Skills ecosystem (agentskills.io). Covers frontmatter migration, repo naming, npx skills add workflow, and making skills work with Claude Code, Codex, Antigravity, Cursor, and 60+ other agents.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: hermes-agent-skill-authoring
  hermes_tags: skills, publishing, agentskills, cross-agent, claude-code, codex, antigravity
  version: 1.0.0
---

# Agent Skills Publishing

Adapt and publish Hermes skills for the open Agent Skills ecosystem so they work
across Claude Code, Codex, Antigravity, Cursor, Cline, and 60+ other agents via
`npx skills add owner/repo`.

## When to Use

- User wants a skill to work with Claude Code, Codex, Antigravity, or other agents
- User mentions `npx skills add`, agentskills.io, skills.sh, or vercel-labs/skills
- User wants to publish a skill repo that any agent can install
- User wants to make a Hermes-specific skill agent-agnostic

## The Open Spec (agentskills.io)

Source of truth: https://agentskills.io/specification

### Directory Structure

```
skill-name/            # dir name MUST match `name` field
├── SKILL.md           # Required
├── scripts/           # Optional
├── references/        # Optional
├── assets/            # Optional
```

### Frontmatter

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | ≤64 chars, lowercase+hyphens, must match parent dir |
| `description` | Yes | ≤1024 chars, what + when, include trigger keywords |
| `license` | No | License name or bundled file ref |
| `compatibility` | No | ≤500 chars, environment requirements |
| `metadata` | No | Arbitrary key-value map |
| `allowed-tools` | No | Space-separated pre-approved tools (experimental) |

### Critical: Hermes vs Spec Frontmatter

Hermes uses top-level `version`, `author`, `tags`. The spec does NOT recognize
these — they must go inside `metadata`:

```yaml
# Cross-agent compatible
---
name: my-skill
description: ...
license: MIT
compatibility: Works with Claude Code, Codex, Antigravity, Hermes. Requires Python 3.12+.
allowed-tools: Bash Read Write Edit
metadata:
  version: "1.0.0"
  author: someone
  tags: foo,bar
---
```

## Adapting a Hermes Skill — Step by Step

1. **Move non-spec frontmatter to `metadata`**: `version`, `author`, `tags`.
2. **Flatten nested metadata — the spec allows ONLY string→string.** Hermes's
   nested `metadata.hermes.*` maps (with list values like `tags: [a, b]`) violate
   the spec. Flatten to scalar keys, comma-joining lists:
   ```yaml
   # Hermes-native (spec-INVALID)          # Spec-valid
   metadata:                                metadata:
     hermes:                                  hermes_tags: "foo, bar"
       tags: [foo, bar]                       hermes_related_skills: "a, b"
       related_skills: [a, b]                 version: "1.0.0"
   ```
   NOTE: flattening breaks Hermes's own nested indexing — normalize in EXPORT
   COPIES only, never in live `~/.hermes/skills/` files.
3. **Add `compatibility`**: List target agents + system requirements.
4. **Add `allowed-tools`**: Generic names — `Bash Read Write Edit`.
5. **Generalize agent-specific instructions**:
   - Hermes `clarify` → "ask the user interactively"
   - `terminal(background=True)` → "run in background or append `&`"
6. **Fix repo/dir naming**: `name` field MUST match parent directory. If repo
   is named differently, either rename the repo (`gh repo rename`) or
   restructure the skill into a matching subdirectory.
7. **Add cross-agent install instructions to README.md**.
8. **Verify with BOTH validators**:
   ```bash
   npx -y skills-ref validate <skill-dir>   # official spec validator
   npx skills add owner/repo --list         # discovery check
   ```
   `skills-ref` is runnable directly via npx (no install). Validate actual
   skill dirs (containing SKILL.md) — pointing it at a category folder fails.

## Batch Export (Monorepo Pattern)

To make a whole library cross-agent at once, build an export monorepo rather
than touching live skills: sync copies from live sources into
`skill_collections/<group>/<category>/<skill>/`, normalizing frontmatter in the
copies only. Working implementation (TDD'd, 69/69 skills-ref-valid):
`~/Documents/Dev/pi-local-dev-exp-v1/src/skill_collections/{normalize,validate,sync}.py`.
Guardrails that mattered: verify body byte-identity after normalization (diff
post-`---`), check normalize idempotence, exclude `.git`/`node_modules` from
skill repos (e.g. graph-flow), record `original_fields` in MANIFEST.json so
migration loses nothing. See `references/spec-compliance-monorepo.md`.

## npx skills add Workflow

```bash
# Install to specific agent
npx skills add owner/repo --agent claude-code
npx skills add owner/repo --agent codex
npx skills add owner/repo --agent antigravity

# Install globally
npx skills add owner/repo -g

# List without installing
npx skills add owner/repo --list

# Use without installing (generates prompt, optionally starts agent)
npx skills use owner/repo --skill my-skill --agent claude-code
```

CLI symlinks by default; use `--copy` for plain copies.

## Agent Feature Matrix

| Feature | Claude Code | Codex | Antigravity | Cursor | Hermes |
|---------|-------------|-------|-------------|--------|--------|
| Basic skills | Yes | Yes | Yes | Yes | Yes |
| `allowed-tools` | Yes | Yes | Yes | Yes | N/A |
| `context: fork` | Yes | No | No | No | N/A |
| Hooks | Yes | No | No | No | N/A |

## Repo Naming Pattern

The repo name should match the skill `name` for clean `npx skills add` UX:

```
# Good: name matches repo
npx skills add rajivmehtaflex/modal-deploy   # repo: modal-deploy, skill name: modal-deploy

# Problem: name mismatches repo
npx skills add rajivmehtaflex/hermes-skill-modal-deploy  # skill name: modal-deploy — MISMATCH
```

Fix with `gh repo rename modal-deploy` (GitHub creates automatic redirects
from the old name, so existing URLs don't break).

## Common Pitfalls

1. **`name` ≠ parent directory.** The spec requires exact match. Rename the repo
   or restructure into a subdirectory.

2. **Top-level `version`/`author`/`tags`.** These are Hermes extensions, not spec
   fields. Move them to `metadata` or cross-agent tools may ignore them.

3. **Agent-specific tool syntax in body.** `terminal(background=True)` or
   `clarify` are Hermes-only. Add generic alternatives alongside.

4. **Forgetting `compatibility`.** Optional but critical for cross-agent
   discoverability — agents use it to decide if a skill will work.

5. **Not testing with `npx skills add --list`.** Always verify the CLI can
   discover the skill before publishing.
