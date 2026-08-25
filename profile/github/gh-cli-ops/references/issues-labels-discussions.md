# Issues, Labels, Discussions

## gh issue

Subcommands: `create`, `list`, `status`, `view`, `close`/`reopen`, `comment`, `edit`, `delete`, `develop` (linked branches), `lock`/`unlock`, `pin`/`unpin`, `transfer`.

```bash
gh issue list -R OWNER/REPO --state open --label bug --limit 30 --json number,title,assignees
gh issue create -R OWNER/REPO --title "T" --body "B" --label bug --assignee @me
gh issue view 123 --json title,body,state,comments
gh issue comment 123 --body "text"            # or -F/--body-file for long text
gh issue close 123                            # --comment "reason"
gh issue transfer 123 OWNER/other-repo
```

Notes:
- Issue arg = number or URL. Repo selection via `-R [HOST/]OWNER/REPO`.
- `--assignee @me` = yourself; `@copilot` assigns Copilot (not on GHES).
- Adding issues to Projects v2 needs the `project` OAuth scope: `gh auth refresh -s project`.
- Non-interactive create: always pass `--title` + `--body` (or `-F body-file`) — otherwise the editor prompt hangs agents.

## gh label

```bash
gh label list -R OWNER/REPO --json name,color,description
gh label create "needs-review" -R OWNER/REPO --color 0E8A16 --description "..."
gh label edit bug --color D93F0B -R OWNER/REPO
gh label delete deprecated -R OWNER/REPO --yes
gh label clone SOURCE-OWNER/SOURCE-REPO          # copy labels into current repo (--force overwrites)
```
`clone` never deletes labels missing from the source; existing ones are skipped unless `--force`.

## gh discussion

Subcommands: `create`, `list`, `view`, `comment`, `edit`. Category is required at creation:

```bash
gh discussion list OWNER/REPO --json number,title,category,url
gh discussion create OWNER/REPO --title "T" --body "B" --category "General"
gh discussion view <number> -R OWNER/REPO --comments
```
