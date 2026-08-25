# Codespaces

Alias: `gh cs`. Subcommands: `list`, `create`, `code` (VS Code), `jupyter`, `ssh`, `cp`, `ports` (+ `forward`, `visibility`), `stop`, `rebuild`, `delete`, `edit`, `logs`, `view`.

```bash
gh codespace list                                        # all your codespaces (name, repo, state)
gh codespace list --repo OWNER/REPO                      # filter
gh codespace ssh -c <codespace-name>                     # interactive shell
gh codespace ssh -c <name> 'echo hello'                  # one-shot remote command
gh codespace cp -r local-dir remote:~/dest/              # scp-like; remote: prefix; -e expands globs
gh codespace ports list -c <name>
gh codespace ports forward -c <name> 8000:8000           # tunnel local:remote
gh codespace stop -c <name>
gh codespace delete -c <name>
gh codespace create -R OWNER/REPO -b branch -m machineTypeSlug
```

Notes:
- `-c/--codespace` names a specific codespace; without it, gh prompts — always pass `-c` in scripts.
- Common filters on most subcommands: `-R user/repo`, `--repo-owner <owner>`.
- `cp` creates an SSH keypair in `~/.ssh` for auth on first use; directories need `-r`.
- Deep SSH setup workflows: see sibling skill `github-codespace-ssh`.
