# Releases, Gists, Orgs, Projects

## gh release

Subcommands: `create`, `list`, `view`, `download`, `upload`, `edit`, `delete`, `delete-asset`, `verify`, `verify-asset`.

```bash
gh release list -R OWNER/REPO --limit 10
gh release view v1.2.0 -R OWNER/REPO --json tagName,publishedAt,assets
gh release create v1.2.0 dist/*.zip --title "v1.2.0" --notes "..."     # auto-creates tag on default branch
gh release create v1.3.0 --target my-branch --generate-notes            # tag from other ref / auto notes
gh release create v1.4.0 --verify-tag                                    # abort if tag doesn't exist
gh release download v1.2.0 -D ./dist                                     # or pattern: -p '*.zip'
```

Notes: asset display labels via trailing `#label`; annotated-tag notes via `--notes-from-tag`; fetch new tag locally with `git fetch --tags origin`.

## gh gist

```bash
gh gist create file.txt --public --desc "..."       # or pipe: cat x | gh gist create
gh gist list --limit 20 --json description,files,updatedAt,visibility
gh gist view <id> [--raw] ; gh gist clone <id> [dir]
gh gist edit/rename/delete <id>
```

## gh org

```bash
gh org list                      # orgs you belong to (paginated)
```

## gh project (Projects v2 — needs `project` scope)

Add scope first if needed: `gh auth refresh -s project`. Commands take a project **number** + `--owner`:

```bash
gh project list --owner OWNER
gh project view 1 --owner OWNER
gh project item-list 1 --owner OWNER
gh project item-add 1 --owner OWNER --url https://github.com/OWNER/REPO/issues/123
gh project item-create 1 --owner OWNER --title "Draft issue"
gh project field-list 1 --owner OWNER
gh project link 1 --owner OWNER --repository OWNER/REPO
```
