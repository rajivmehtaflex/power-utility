# Hermes home audit notes

This note captures a real inspection pattern for `~/.hermes` and the important classification rule discovered while auditing the folder.

## High-value safe cleanup candidates
- `~/.hermes/logs/` — runtime logs, safe to remove if not needed for debugging.
- `~/.hermes/cache/`, `~/.hermes/bootstrap-cache/`, `~/.hermes/image_cache/`, `~/.hermes/audio_cache/` — cache directories.
- `~/.hermes/**/__pycache__/` and `~/.hermes/**/*.pyc` — Python bytecode caches.
- `~/.hermes/.DS_Store` — Finder metadata.
- `~/.hermes/.update_check`, `~/.hermes/.skills_prompt_snapshot.json` — small maintenance artifacts.
- `~/.hermes/hermes-agent/.git/objects/pack/tmp_pack_*` — Git temp pack files; treat as garbage only when they are clearly `tmp_pack_*`.
- `~/.hermes/hermes-agent/apps/desktop/release/` and `apps/desktop/dist/` — generated build outputs in this checkout.

## Keep / protect by default
- `~/.hermes/config.yaml`
- `~/.hermes/.env`
- `~/.hermes/state.db*`
- `~/.hermes/auth.json`
- `~/.hermes/skills/`
- `~/.hermes/sessions/`
- `~/.hermes/profiles/`
- `~/.hermes/memories/`
- `~/.hermes/shared/`
- `~/.hermes/kanban.db`

## `~/.hermes/hermes-agent/` findings
Top-level heavy hitters from one inspection:
- `.git` ~672.9MB before maintenance; `git gc` later reduced it to ~273MB
- `apps` ~360.5MB
- `node_modules` ~275.8MB
- `venv` ~251.9MB

Important nuance:
- `apps/desktop/release/` and `apps/desktop/dist/` are generated build outputs and are usually rebuildable.
- `node_modules/` is **not automatically safe** in this checkout.
  - The repo’s runtime/build scripts reference it.
  - `apps/desktop/electron/main.cjs` falls back to `node_modules` for `node-pty` in dev mode.
  - `apps/desktop/scripts/assert-root-install.cjs` checks for root `node_modules/vite/package.json`.
  - Therefore, deleting root `node_modules/` can break source checkout runtime/build until dependencies are reinstalled.
- `venv/` is usually recreateable, but only if you are comfortable rebuilding the Python environment.
- `git gc` is a useful separate phase for a large `.git/` object store; verify with `git count-objects -vH` and `du -sh .git` after the run.

## Cleanup execution pattern
1. Remove safe filesystem junk first (`logs`, caches, `__pycache__`, `*.pyc`, temp packs, build output).
2. Then consider Git maintenance (`git gc`) if `.git/objects` is large.
3. Re-measure after each phase and report the reclaimed space separately, plus the total.
4. If the user asks for a cleanup summary, include a short one-line “space gained” answer at the end.

## Best practice for future audits
1. Inspect top-level sizes first.
2. Drill into the largest subtree.
3. Use `git check-ignore -v` and repo scripts to validate whether a directory is generated or runtime-critical.
4. Put `node_modules/`, `venv/`, `release/`, and `dist/` into "ask me first" unless the user explicitly wants to rebuild later.
