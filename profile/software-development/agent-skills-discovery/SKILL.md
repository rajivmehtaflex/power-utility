---
name: agent-skills-discovery
description: Discover and install Agent Skills via npx and gh skill.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: cross-agent-skills, agent-skills-publishing, github-repo-management
  hermes_tags: skills, agent-skills, discovery, gh-skill, npx-skills, exa, runpod
  version: 1.0.0
---

# Agent Skills Discovery — Dual-Manager Verification

Discover and install Agent Skills from either package manager and verify they actually exist before installing. Covers the two interoperable managers that share the Agent Skills spec (`agentskills.io`): `npx skills add` (Vercel/skills.sh) and `gh skill` (GitHub CLI v2.90+, preview).

## When to Use

- User asks "does {tool} have a skill?" (e.g., RunPod CLI, gh CLI, Docker, HuggingFace)
- User wants to install a skill but is unsure which repo/skill name is canonical
- Need to compare `runpod/runpod-plugins-official` vs legacy `runpod/skills`, or similar forks
- User mentions `npx skills add`, `gh skill`, `skills.sh`, or `agentskills.io`
- Verifying a skill before recommending an install in docs or chat

## The Two Managers

Both read the same `SKILL.md` spec; skills are interoperable. Prefer `gh skill` when the user already has `gh` auth and wants search/preview/pinning via git tags; prefer `npx skills add` for auto-detection across 50+ agents.

### npx skills add (Vercel)

```bash
# List without installing
npx skills add owner/repo --list

# Install (auto-detect agents) / specific agent / global
npx skills add owner/repo
npx skills add owner/repo --skill my-skill --agent codex --global
npx skills add owner/repo --skill my-skill --agent claude-code --global

# Copy vs symlink (CI/containers)
npx skills add owner/repo --copy
```

### gh skill (GitHub CLI v2.90+, preview — subject to change)

```bash
gh skill search <keyword>              # search across GitHub (e.g., gh skill search runpod)
gh skill preview owner/repo [skill]    # preview SKILL.md + assets without installing
gh skill install owner/repo [skill[@tag]] [--agent <agent>] [--scope user|project]
gh skill list                          # list installed across all agent dirs
gh skill update --all
gh skill publish --dry-run             # validate before publishing
# Alias: gh skills == gh skill
```

`gh skill` writes to `.agents/skills/` (project scope, shared by Copilot/Cursor/Codex/Gemini etc.) or user scope; supports version pinning via `@tag` (git tag/release).

## Workflow — Verify Before Install

### Step 1 — Exa search for canonical source

Use a semantically rich query — Exa is the primary verification before touching `gh`:

```bash
# via deferred tool mcp__exa__web_search_exa
query="runpod.io RunPod CLI skills offer skills.sh agent skills"  # for RunPod
query="GitHub CLI gh skills agent skills skills.sh"               # for gh
query="<tool> agent skill teaches agent to use <tool> CLI"
numResults=15
```

Parse plain text result (NOT JSON). Extract `Title:` / `Published:` / `Highlights:`. Collapse duplicates with same title + >60% highlights overlap; keep the most complete hit.

**Canonical hits discovered this session:**
- RunPod: `docs.runpod.io/get-started/agent-skills` (19/08/2026) + `github.com/runpod/runpod-plugins-official` (official, 6 skills) vs legacy `runpod/skills` (2 skills)
- gh: `cli.github.com/manual/gh_skill`, GitHub Changelog `Manage agent skills with GitHub CLI` (16/04/2026), `cli/cli/pull/13244` (adds `skills/gh` + `skills/gh-skill` lean guides)

If Exa returns `N/A` for Published, infer from highlights or use retrieval date; always normalize to `dd/mm/yyyy` for tables.

### Step 2 — Confirm with gh skill search + preview (live)

```bash
gh auth status                         # ensure correct account if multi-account setup
gh --version                           # need >=2.90.0 for gh skill
gh skill search <keyword>              # e.g., gh skill search gh | head -n 40
gh skill preview owner/repo [skill]    # read the lean guide before installing
# Large preview may page — pipe through head or read full output
```

Examples verified live:
```bash
gh skill search gh
# -> Cogni-AI-OU/cogni-ai-agent-skills  gh  (3 skills) …
gh skill preview cli/cli gh            # lean guide: --json/--jq, pagination -L/--paginate, --repo targeting
gh skill preview openclaw/skills github-cli
```

### Step 3 — Install (copy-paste ready)

Provide both managers so the user can choose:

```bash
# RunPod — official bundle (router + 6 skills)
npx skills add runpod/runpod-plugins-official
# or just the CLI lane
npx skills add https://github.com/runpod/runpod-plugins-official/tree/main/plugins/runpod/skills/runpodctl

# CLI dependency (skills call it)
curl -sSL https://cli.runpod.net | bash   # or: brew install runpod/runpodctl/runpodctl
export RUNPOD_API_KEY=<key> && runpodctl doctor

# gh lean guides (official)
gh skill install cli/cli gh
gh skill install cli/cli gh-skill
```

### Step 4 — Verify install

```bash
gh skill list
npx skills add owner/repo --list       # should now show as installed
gh api repos/owner/repo --jq '{description, homepage, topics}'  # for repo-profile checks
```

## Capability Matrix — npx vs gh

| Capability | `npx skills add` | `gh skill` |
|---|---|---|
| Search | No (use `gh skill search` or Exa) | Yes — `gh skill search` |
| Preview | `--list` (list only) | Yes — `gh skill preview` (full SKILL.md) |
| Install scope | `--global` (user) or project | `--scope user|project` + `--agent <name>` |
| Version pin | `@tag` via `npx skills add repo@tag` (limited) | `skill@tag` via git tag |
| Update | re-run add | `gh skill update --all` |
| Auth | none (public clones) | `gh auth` (needed for private repos, rate limits) |

## Inventorying Installed Skills — Bundled vs User-Added

When asked "which skills did I install/create?" (as opposed to what ships with Hermes), do NOT guess from folder names, authors, or timestamps — Hermes keeps an authoritative manifest:

```bash
# Ground truth: bundled skill names as "name:content-hash"
cut -d: -f1 ~/.hermes/skills/.bundled_manifest | sort > /tmp/bundled.txt

# Everything on disk (maxdepth 3 catches category/ subdirs!)
find ~/.hermes/skills -maxdepth 3 -name SKILL.md \
  | sed "s|$HOME/.hermes/skills/||; s|/SKILL.md||" \
  | awk -F/ '{print $NF}' | sort > /tmp/disk.txt

comm -23 /tmp/disk.txt /tmp/bundled.txt   # = user-installed
```

Gotchas learned the hard way:
- Use `find -maxdepth 3`, not `-maxdepth 2` — nested categories (`devops/modal-deploy`) get missed otherwise and you undercount badly (real case: reported 7 user skills when the true count was 69).
- Author fields lie (`author: Hermes Agent` appears on third-party skills) and timestamps only show install date, not provenance. Only the manifest diff is reliable.
- Also check `~/.agents/skills/` (cross-agent shared dir) and any loose workspace `Skills/` folders for skills outside the profile.
- Failed installs leave nothing behind: if `npx skills add ... --skill X` reports "No matching skills found", verify with `ls ~/.agents/skills` + project dir + npx cache before claiming residue exists — usually there is none to roll back.

## Pitfalls

1. **Legacy vs official repo.** `runpod/skills` (2 skills) is superseded by `runpod/runpod-plugins-official` (1 plugin, 6 skills). Always prefer the `-official` repo; Exa may return both — check the README's skill table.
2. **Spillover large results.** Exa `web_search_exa` returns >50KB and the tool saves the full output to `~/.hermes/cache/spillover/call_*.txt` with a JSON wrapper (`{"result":"..."}`). Do NOT `json.loads` the inner text as JSON — parse the wrapper then treat `result` as plain text with `Title:/URL:/Published:/Highlights:` entries split on `\n---\n`.
3. **gh skill preview 404.** `openclaw/skills` has no `github-cli` at the guessed path — preview fails with `could not determine default branch: 404`. Fall back to `npx skills add openclaw/skills --list` or Exa.
4. **Multi-account gh.** `gh auth status` may show 4 accounts (rajivmehtapy primary, rajivmehtaflex, etc.). Run `gh auth switch --user <owner>` before `gh skill install` targeting a repo owned by that account.
5. **Project scope confusion.** `gh skill install` without `owner/repo` prefix or when run from a workspace root infers repo from `cwd` remotes — always pass explicit `owner/repo` when verifying from a parent workspace.
6. **Date normalization.** Exa highlights may contain relative dates ("7 hrs ago") — convert to `dd/mm/yyyy` using retrieval date.
7. **Requested skill name may not exist — always `--list` first on big repos.** `npx skills add https://github.com/github/awesome-copilot --skill gh-cli` cloned fine (413 skills) then failed with "No matching skills found for: gh-cli". The clone is ephemeral (auto-deleted), so a failed attempt leaves zero residue. Workflow: run with `--list`, grep the output for candidate names, THEN install the exact name (`gh-attach` / `github-issues` existed; `gh-cli` did not). Parsing tip: the list output uses box-drawing chars — skill names sit alone on lines matching `"    [a-z0-9-]+$"` after stripping.
8. **Node version warning is non-fatal.** Running npx under Node v24 prints "npm v12 does not support Node.js v24" but `skills add` still works. No need to switch to nvm Node 22 for this tool.
9. **Agent-detection makes it non-interactive.** When run from Hermes, the CLI prints "Agent detected — installing non-interactively" and never blocks on prompts — safe to run from the agent terminal without a pty.

## References

- `references/dual-manager-matrix.md` — full npx vs gh verb table with RunPod/gh worked examples
- `references/exa-skill-verification.md` — Exa query templates and spillover parsing recipe
- `references/repo-profile-from-readme.md` — deriving GitHub repo About description/homepage/topics from README.md via `gh repo edit` + `gh api` verification (companion pattern used with skill installs)

## Verification Checklist

- [ ] Exa search executed with semantically rich query (`<tool> agent skill ...`) and highlights parsed as plain text
- [ ] `gh skill search` + `gh skill preview` confirm canonical repo/skill name and that `gh --version` >=2.90.0
- [ ] Both install paths provided (`npx skills add` and `gh skill install`) with scope/agent flags
- [ ] No URLs leaked into user-facing tables (Exa Content is URL-free)
- [ ] Post-install verification command included (`gh skill list` / `gh api`)
