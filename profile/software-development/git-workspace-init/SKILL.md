---
name: git-workspace-init
description: Make a root git repo over nested repos; skip gitlink traps.
metadata:
  author: Hermes Agent
  version: 1.0.0
---

# Git Workspace Init (root repo over nested repos)

## When to use
- The user asks to "initialize a git repo" in a folder that already contains many
  subproject directories, each of which has its own `.git`.
- Common in workspace/monorepo layouts where subprojects are independent (separate
  remotes, branches, gh accounts) but the root holds shared reference material,
  notes, and scripts.

## Goal
Create ONE git repo at the root that tracks only the top-level loose files
(notes, scripts, `.gitignore`, `AGENTS.md`), and leaves every subfolder
independent (each keeps its own `.git` and history).

## Steps
1. `cd` into the root directory.
2. Write `.gitignore` FIRST — before any `git add`. Exclude:
   - Every nested-repo folder by name, with a trailing slash (e.g. `adk-exp/`,
     `Skills/`, `g-xero-api/`). Trailing slash means git never descends.
   - OS/editor cruft: `.DS_Store`, `.vscode/`.
   - Python: `__pycache__/`, `.venv/`, `env/`, `.env`, `*.egg-info/`, `dist/`,
     `build/`.
   - Secrets: `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa`, `id_ed25519`,
     `known_hosts`.
3. `git init`
4. `git add -A`  (ignore rules are now in effect, so nested repos are skipped)
5. `git status --short` — confirm only top-level files are staged.
6. `git commit -m "Initial import: top-level files only; subfolders keep their own repos"`
7. Add a root `AGENTS.md` documenting the layout and the "one root repo,
   independent subprojects" convention.

## Pitfalls (this is where it goes wrong)
**Gitlink trap.** If you run `git add -A` BEFORE writing `.gitignore`, git sees
each nested `.git` and adds it as a *gitlink* (mode `160000`, a submodule-like
pointer). Writing `.gitignore` afterward does NOT retroactively remove already-
staged gitlinks. Symptoms:
- `git status` shows `?? SubProj/` (untracked, because now ignored) AND
  `D  SubProj` (a staged deletion of the gitlink that is still in HEAD).
- `git ls-tree --name-only -r HEAD` still lists `SubProj`.

**Fix:**
```
git rm --cached --ignore-unmatch <SubProj>
git rm --cached --ignore-unmatch <SubProj>/<nested>
git add <other-new-files>        # e.g. AGENTS.md
git commit -m "Clean root index: drop nested-repo gitlinks, add AGENTS.md"
```
After this, `git status` shows only the two intentional `??` dirs, nothing staged dirty.

**Do NOT add nested repos as submodules** unless the user explicitly wants
submodules. The `git add` "embedded repository" warning is a hint, not a command.

## Verification (run a script, don't eyeball)
Use `scripts/verify_root_repo.py` from the repo root. It asserts:
- No nested-repo prefix appears in `git ls-files` (index) or
  `git ls-tree --name-only -r HEAD` (committed tree).
- The expected top-level files ARE tracked.
Run: `python3 scripts/verify_root_repo.py` (repo root via cwd or `--repo`).

## Notes
- A local-only install has no remote. Ask which gh account to add a remote on
  (session example: active `rajivmehtaflex`; other remotes `rajivmehtapy`).
- `git status` still lists ignored nested dirs as `??` because they have their
  own `.git`. To silence entirely: `git config set --local status.showUntrackedFiles no`
  or add explicit ignore lines. This is cosmetic, not a defect.
