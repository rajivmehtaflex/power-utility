# Exit Codes & Output Formatting

## Exit codes (from `gh help exit-codes`)

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | failure |
| 2 | cancelled while running |
| 4 | authentication required |

Individual commands may add more — check a command's docs if scripting on exit codes. Note: `gh auth status` exits 1 if *any* account has auth issues, but always exits 0 with `--json`.

## Formatting pipeline (`gh help formatting`)

Most commands: default plain text → `--json <fields>` → `--jq '<expr>'` or `--template '<go-tmpl>'`.

- **Discover fields**: run with bare `--json` (no args) to list valid field names.
- `--jq` is built in (no local jq install needed); pretty-prints on a TTY.
- `--jq` + `--template` require `--json` to be present.
- Go template extras: `pluck`, `join`, `color`, `timeago`, `timefmt`, `truncate`, `tablerow`, `hyperlink`; Sprig: `contains`, `hasPrefix`, `regexMatch`, …

```bash
# Select
gh pr list --json number,title --jq '.[] | "\(.number) \(.title)"'
# Filter
gh issue list --json number,title,labels --jq 'map(select((.labels | length) > 0))'
# Template table
gh api repos/{owner}/{repo}/issues --template '{{range .}}{{tablerow .number .title}}{{end}}'
```

Scripting tips:
- Pipe-friendly by default; set `GH_FORCE_TTY=80` for terminal-style output when redirected, or empty `GH_PAGER=` to suppress paging.
- `NO_COLOR=1` / `CLICOLOR=0` strip ANSI codes for clean machine parsing.

## Environment quick reference (`gh help environment`)

Auth: `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GH_HOST`, `GH_REPO`.
Behavior: `GH_DEBUG=api`, `GH_PROMPT_DISABLED`, `GH_PAGER`, `GH_CONFIG_DIR`, `GH_NO_UPDATE_NOTIFIER`.
Display: `NO_COLOR`, `CLICOLOR`, `GH_FORCE_TTY`, `GH_MDWIDTH`.
