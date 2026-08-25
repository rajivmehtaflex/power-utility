# Actions: Runs, Workflows, Caches

## gh run — workflow runs

Subcommands: `list` (alias `ls`), `view`, `watch`, `rerun`, `cancel`, `delete`, `download`.

```bash
gh run list --limit 10 --json databaseId,name,status,conclusion,headBranch,event,url
gh run list -w ci.yml --branch main -s failure          # filter by workflow/branch/status
gh run view <run-id>                                     # summary + jobs
gh run view <run-id> --log-failed                        # logs of failed steps only
gh run watch <run-id> --exit-status                      # block until done; nonzero if failed
gh run rerun <run-id> --failed                           # only failed jobs (with dependencies)
gh run cancel <run-id>
gh run download <run-id>                                 # artifacts → ./artifacts by default; -n name -D dir
```

Gotchas:
- `-w <workflow>` misses disabled workflows — add `-a/--all`.
- `rerun --job` needs the **databaseId**, not the number from the browser URL:
  get IDs via `gh run view <run-id> --json jobs --jq '.jobs[] | {name, databaseId}'`.
- PR-scoped CI state belongs to `gh pr checks <num> --watch`, not `run list`.
- Status values include queued/in_progress/completed + conclusions success/failure/cancelled/skipped/timed_out…

## gh workflow

```bash
gh workflow list --all                    # incl. disabled
gh workflow view ci.yml                   # or numeric ID; shows badge + recent runs
gh workflow run ci.yml --ref my-branch -f key=value    # trigger via workflow_dispatch
gh workflow enable/disable <name-or-id>
```

## gh cache

```bash
gh cache list -R OWNER/REPO
gh cache delete <cache-id-or-key>         # scope with --ref refs/heads/<branch>
gh cache delete --all                     # needs repo scope
```
