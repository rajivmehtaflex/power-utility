---
name: gh-cli-ops
description: Use for any gh CLI or GitHub-via-terminal task; routes refs.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: github-auth, github-pr-workflow, github-code-review, github-issues, github-repo-management, github-codespace-ssh, codebase-inspection
  hermes_tags: GitHub, gh-cli, CLI, Automation
  platforms: linux, macos, windows
  version: 1.0.0
---

# gh CLI Operations (gh-cli-ops)

## When to use

Load this skill whenever a task involves the `gh` CLI or doing GitHub work from the terminal: checking/switching accounts, calling the GitHub API, searching GitHub, repos, PRs, issues, Actions runs, secrets/variables, releases, gists, Projects, or codespaces. It routes each task to the right command group and reference file.

Command map + operational conventions for `gh` (verified against **gh v2.98.0**). Deep workflows live in sibling `github-*` skills — this skill routes to them and covers everything they don't.

## Routing table: task → command group → reference

| Task | Command group | Details |
|------|--------------|---------|
| Which account am I? / switch account / login / token / scopes | `gh auth` | [references/auth-and-config.md](references/auth-and-config.md) |
| gh settings (git_protocol, editor, pager…), env vars | `gh config` / environment | [references/auth-and-config.md](references/auth-and-config.md) |
| Call any REST/GraphQL endpoint, paginate | `gh api` | [references/api-and-search.md](references/api-and-search.md) |
| Search code/commits/issues/PRs/repos across GitHub | `gh search` | [references/api-and-search.md](references/api-and-search.md) |
| Clone/create/fork/view/sync/delete repos | `gh repo` | [references/repos-and-prs.md](references/repos-and-prs.md) |
| Create/list/check/merge/checkout PRs | `gh pr` (alias `co` = checkout) | [references/repos-and-prs.md](references/repos-and-prs.md) |
| Issues, labels, discussions | `gh issue`, `gh label`, `gh discussion` | [references/issues-labels-discussions.md](references/issues-labels-discussions.md) |
| Workflow runs, logs, watch, caches, enable/disable workflows | `gh run`, `gh workflow`, `gh cache` | [references/actions-runs-workflows.md](references/actions-runs-workflows.md) |
| Codespaces: list, ssh, stop, ports | `gh codespace` | [references/codespaces.md](references/codespaces.md) |
| Actions secrets & variables, SSH/GPG keys | `gh secret`, `gh variable`, `gh ssh-key`, `gh gpg-key` | [references/secrets-vars-keys.md](references/secrets-vars-keys.md) |
| Releases, gists, orgs, Projects v2 | `gh release`, `gh gist`, `gh org`, `gh project` | [references/releases-gists-orgs-projects.md](references/releases-gists-orgs-projects.md) |
| Extensions, aliases, rulesets, attestations, browse | misc commands | [references/extensions-misc.md](references/extensions-misc.md) |
| Exit codes, JSON formatting (--json/--jq/--template) | help topics | [references/exit-codes-formatting.md](references/exit-codes-formatting.md) |

## Conventions that apply everywhere

1. **JSON output**: most listing/view commands accept `--json <fields>,... --jq '<expr>'`. Omit the field list (`--json`) to see valid fields. jq is built in — no local jq needed.
2. **Target a repo without cd'ing**: append `-R HOST/]OWNER/REPO` (supported by pr/issue/release/run/etc.) or export `GH_REPO=OWNER/REPO`.
3. **Headless/non-interactive**: interactive prompts hang agents. Prefer explicit flags (`--repo`, `--user`, `-R`) over prompts; set `GH_PROMPT_DISABLED=1` if needed.
4. **Auth via env**: `GH_TOKEN` overrides stored credentials on github.com; `GH_HOST`+`GH_TOKEN` for Enterprise. Fine-grained PATs: use `GH_TOKEN`, not `gh auth login --with-token`.
5. **Exit codes**: 0 ok · 1 fail · 2 cancelled · 4 auth required. See [references/exit-codes-formatting.md](references/exit-codes-formatting.md).
6. **Debugging**: `GH_DEBUG=1` (or `GH_DEBUG=api` for HTTP traces).

## Multi-account pattern (this machine has 4 accounts)

```bash
gh auth status                    # list accounts + which is active
gh auth switch --user <name>      # make another stored account active
gh auth token --user <name>       # print a specific account's token
```
Accounts: rajivmehtapy (primary), rajivmehtaflex, rajivmehtajs, mantramehtapy. Before push/PR work as a specific identity: check `gh auth status`, switch if needed (`gh auth switch --user <account>`), verify with `gh api user --jq .login`.

## When to hand off to sibling skills

- Auth *setup* (new machine, tokens, SSH keys): `github-auth`
- Full PR lifecycle (branch → PR → CI → merge): `github-pr-workflow`
- PR review comments: `github-code-review`
- Issue triage/creation at scale: `github-issues`
- Repo create/fork/mirror ops: `github-repo-management`
- Codespace SSH setup: `github-codespace-ssh`

## Regenerating the command corpus

Full `--help` dump used to build this skill: regenerate with `scripts/gh_help_crawl.sh` from the pi-local-dev-exp-v1 workspace (`./scripts/gh_help_crawl.sh gh_cli_help.md`). Re-run after gh upgrades; update the version pin above.