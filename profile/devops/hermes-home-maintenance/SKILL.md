---
name: hermes-home-maintenance
description: Audit and clean ~/.hermes safely by separating core state from caches, logs, and rebuildable artifacts.
license: MIT
metadata:
  author: Hermes Agent
  hermes_tags: hermes, home, cleanup, audit, disk-usage, maintenance
  platforms: macos, linux
  version: 0.1.0
---

# Hermes Home Maintenance

Use this skill when a user wants to inspect, audit, or shrink `~/.hermes` without breaking Hermes.

## Goals
- Identify what is **core state** vs **safe-to-delete cache/output**.
- Produce a concise **keep / delete safely / ask me first** breakdown.
- Treat the Hermes source checkout under `~/.hermes/hermes-agent/` as a special case: some subtrees are rebuildable, others are required for runtime or local development.

## Default workflow
1. **Inventory the tree first**
   - Get top-level size/counts, then drill into the largest subtrees.
   - Look for caches, logs, temp files, build outputs, and package-manager artifacts.
2. **Classify paths**
   - **Keep:** config, secrets, session state, auth, profiles, skills, memories, and source code.
   - **Delete safely:** logs, `__pycache__`, `*.pyc`, cache folders, `.DS_Store`, lock/tmp artifacts, and obvious generated files.
   - **Ask first:** anything inside a source checkout that looks like dependencies or build output until you verify it is rebuildable.
3. **Verify before recommending deletion**
   - If the path is inside a repo checkout, check whether it is gitignored and whether build scripts or runtime code reference it.
   - For Node/Python project trees, confirm whether a directory is used by dev/runtime before calling it junk.
4. **Report in tables**
   - Include path, size, category, and recommendation.
   - If a user specifically asked for cleanup advice, separate “safe now” from “ask me first.”
5. **If cleanup is executed, verify the savings in phases**
   - Run filesystem deletions first, then any Git maintenance (for example `git gc`) as a separate step.
   - Re-measure after each phase so the user gets an honest reclaim figure for deletions, Git maintenance, and the total.
   - Prefer reporting both the remaining size and the reclaimed delta instead of only saying a command succeeded.
   - Report the bytes actually deleted separately from the final net size change: a running Hermes process may immediately recreate logs, caches, `.update_check`, and Python bytecode.

## Live-process cleanup guard

Before deleting anything below `$HERMES_HOME`, inspect running processes and open files with `pgrep` and `lsof`. If Hermes Desktop, the gateway, or a profile process is running:

- Never delete an open log, database sidecar, runtime binary, or dependency file.
- Either stop Hermes cleanly before cleanup, or skip open paths and explicitly report them as skipped.
- Expect cache markers, logs, and `__pycache__` files to be recreated while Hermes remains active; perform a final inventory after the verification smoke test.
- Keep the cleanup scope conservative when the current desktop/gateway session cannot be stopped without interrupting the user.

## Guard implementation details

Use exact protected paths and protected roots rather than rejecting every path whose basename happens to be `skills`, `profiles`, or `shared`. For example, protect `$HERMES_HOME/skills/`, `$HERMES_HOME/profiles/`, and `$HERMES_HOME/memories/`, while still allowing deliberate, separately verified cleanup of a profile's `logs/` directory. Always resolve paths and refuse anything outside `$HERMES_HOME` before unlinking or removing a directory.

A safe cleanup report should include: candidate count/bytes before deletion, open paths skipped, removed count/bytes by category, recreated candidates after verification, protected-path existence, database integrity results, and the final `hermes doctor` result.

See `references/live-process-safe-cleanup.md` for the macOS guard and accounting pattern.

See `references/checkpoint-workflow.md` for the distinction between Hermes config/state snapshots and filesystem checkpoints, supported inspection commands, and the automatic mutation-triggered checkpoint workflow.

## Important pitfalls
- `node_modules/` is **not automatically safe** in a Hermes source checkout.
  - It may be needed for dev/runtime, local desktop execution, or packaging.
  - Only recommend removing it when you have verified it is purely a reinstallable dependency tree and the user is fine reinstalling later.
- Build outputs such as `dist/`, `release/`, and similar app packaging folders may be safe **only if** they are generated and rebuildable.
- Git temp pack files can be removable, but verify they are temporary (`tmp_pack_*`) before deletion.
- Don’t classify core Hermes state like `config.yaml`, `.env`, `state.db`, `auth.json`, `skills/`, `sessions/`, or `profiles/` as cleanup candidates.

## npm global packages: cleanup pattern
When auditing disk usage in `~/.npm` or `~/.npm-global`, list largest packages with:
```bash
du -sh ~/.npm/*/node_modules/*/.package-lock.json 2>/dev/null | sort -rh | head -20
```
If a global package has a stale `node_modules` but the binary is already updated by `npm update -g`, the old version's `.package-lock.json` is safe to remove after `npm cache clean --force`.

## Output format
Prefer a compact table with columns like:
- `Path`
- `Size`
- `Class`
- `Recommendation`
- `Reason`

Then add a short “largest space users” summary if helpful.

## Session-specific reference
See `references/hermes-home-audit.md` for an example classification from an actual `~/.hermes` inspection, including which `hermes-agent` subtrees were rebuildable and which ones were runtime-sensitive.
