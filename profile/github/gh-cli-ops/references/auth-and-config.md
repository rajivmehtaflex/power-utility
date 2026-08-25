# Auth & Config

## gh auth — accounts and credentials (v2.98.0)

| Subcommand | Purpose |
|---|---|
| `gh auth status` | Show all known accounts per host + which is **active**; exits 1 if any account has auth issues (unless `--json`) |
| `gh auth switch` | Change the active account for a host |
| `gh auth login` | Web flow (`-w`) or `--with-token < file` (classic PAT needs scopes: `repo`, `read:org`, `gist`) |
| `gh auth logout` | Remove stored credentials locally (**does not revoke** the token server-side) |
| `gh auth refresh` | Add/remove OAuth scopes: `-s write:org`, `--remove-scopes delete_repo`, `--reset-scopes`. Must be active account — switch first |
| `gh auth token` | Print token for host/account (`-u <user>`) — never print into shared logs |
| `gh auth setup-git` | Configure git credential helper to use gh |

### Multi-account workflow

```bash
gh auth status                       # who exists, who is active
gh auth switch --user rajivmehtajs   # activate another stored account
gh api user --jq .login              # verify active identity
gh auth token --user rajivmehtaflex  # that account's token
```

Notes from help text:
- `--with-token` is discouraged for fine-grained PATs — set `GH_TOKEN` instead.
- `gh auth status --json hosts --jq '.hosts | add'` → flat array of account states.
- Refreshing an inactive account requires switching to it first.

## gh config

```bash
gh config list                     # all settings (alias: gh config ls)
gh config get git_protocol         # one key
gh config set git_protocol ssh     # set key
gh config clear-cache              # clear cli cache
```

Keys: `git_protocol {https|ssh}`, `editor`, `prompt {enabled|disabled}`, `pager`, `browser`, `http_unix_socket`, `color_labels`, `accessible_colors`, `accessible_prompter`, `spinner`, `telemetry {enabled|disabled|log}`. Per-host with `-h/--host`.

## Key environment variables

- `GH_TOKEN` / `GITHUB_TOKEN` — token override for github.com (precedence over stored creds)
- `GH_ENTERPRISE_TOKEN` / `GITHUB_ENTERPRISE_TOKEN` — for GHES hosts
- `GH_HOST` — target hostname when not inferable
- `GH_REPO` — `[HOST/]OWNER/REPO` so repo-scoped commands work outside a git checkout
- `GH_DEBUG=1|api` — verbose / HTTP trace · `GH_PROMPT_DISABLED=1` — no interactive prompts
- `GH_PAGER`/`PAGER` — set empty to disable paging in scripts · `NO_COLOR=1`
- `GH_CONFIG_DIR` — default `$HOME/.config/gh`

Full list: run `gh help environment`.
