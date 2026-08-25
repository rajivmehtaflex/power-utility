# Extensions & Misc Commands

## gh extension

```bash
gh extension list
gh extension browse / search <query>
gh extension install OWNER/gh-<name>
gh extension upgrade [<name>|--all]
gh extension remove <name>
gh extension create <name>        # scaffold a new Go/bash extension repo
```
Extensions are executables named `gh-*`; invoked as `gh <name>`. Env `GH_EXTENSION=1` is set when run via gh.

## gh alias

```bash
gh alias list
gh alias set co 'pr checkout'
gh alias delete co
gh alias import aliases.yml       # bulk
```
Built-in: `gh co` = `gh pr checkout`.

## gh ruleset

```bash
gh ruleset list -R OWNER/REPO            # or --org OWNER
gh ruleset view <ruleset-id>
gh ruleset check <branch-name>           # which rulesets apply to a branch
```

## gh attestation

Artifact attestations (supply-chain): `gh attestation verify <file> -R OWNER/REPO`, `download`, `trusted-root`.

## gh browse

Open github.com in browser from context:
```bash
gh browse                       # current repo; subpaths: gh browse issues / pulls
gh browse 123                   # issue/PR number; -b branch; --settings; path:line refs
```

## gh status

Cross-repo dashboard of your work (assigned issues/PRs, review requests, mentions, activity): `gh status`, `-o org` to scope, `-e owner/repo` to exclude.

## One-liners

- `gh completion -s bash|zsh|fish` — shell completions
- `gh copilot` — Copilot CLI suggest/explain (preview)
- `gh preview` — preview-flagged features (e.g. `gh preview prompter`)
- `gh agent-task` — cloud agent tasks (create/list/view, preview)
- `gh skill` — install/manage agent skills from registries (preview)
- `gh licenses` — view gh's dependency licenses
- `gh telemetry` — telemetry on/off/status

- Anything without a dedicated command → `gh api` with the REST path (see api-and-search.md).
