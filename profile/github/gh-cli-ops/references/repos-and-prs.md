# Repos & PRs

## gh repo

Subcommands: `create` (alias `new`), `list`, `clone`, `fork`, `view`, `edit`, `archive`/`unarchive`, `delete`, `rename`, `sync`, `set-default`, `deploy-key`, `autolink`, `gitignore`, `license`, `read-dir`, `read-file` (preview).

```bash
gh repo create my-project --public --clone          # new + clone
gh repo create my-project --private --source=. --remote=origin --push   # from local dir
gh repo list rajivmehtapy --limit 50 --json name,visibility,updatedAt
gh repo view OWNER/REPO --web                        # accepts OWNER/REPO or URL
gh repo clone cli/cli
gh repo sync OWNER/REPO                              # sync a fork
gh repo set-default OWNER/REPO                       # for dirs with multiple remotes/forks
gh repo read-file OWNER/REPO path/to/file            # read remote file (preview)
```

Notes: omitting `OWNER/` in create defaults to the active authenticated user — check `gh auth status` first on multi-account machines. `--push` mirrors all refs from a bare source.

## gh pr

Subcommands: `create`, `list`, `status`, `checkout` (global alias `co`), `checks`, `close`, `comment`, `diff`, `edit`, `lock`/`unlock`, `merge`, `ready` (`--undo` → draft), `reopen`, `revert`, `review`, `update-branch`, `view`.

```bash
gh pr create --title "T" --body "B" --base main        # non-interactive; --fill pulls commit info
gh pr list --state open --limit 20 --json number,title,headRefName,isDraft
gh pr status                                            # yours: authored, assigned, review-requested
gh pr checks 123 --watch                                # block until CI finishes
gh pr checkout 123                                      # or: gh co 123
gh pr diff 123                                          # patch text; --name-only for file list
gh pr merge 123 --squash --delete-branch                # or -m / -r; --auto waits for checks
gh pr review 123 --approve --body "lgtm"                # or --request-changes / --comment
gh pr update-branch                                     # merge base into PR branch
```

Key flags/notes:
- Without an argument, most `pr` commands select the PR belonging to the current branch.
- `merge`: exactly one of `-m/--merge`, `-r/--rebase`, `-s/--squash`; `--auto` enables auto-merge once required checks pass; `--admin` bypasses requirements; `--match-head-commit SHA` guards races; merge-queue branches need no strategy flag.
- `create`: use `--fill` (first-commit subject+body) or explicit `--title/--body` to avoid the interactive editor hanging agents; `--draft` available; `-F/--body-file -` reads body from stdin.
- Repo selection: `-R HOST/]OWNER/REPO` works across all pr subcommands.
