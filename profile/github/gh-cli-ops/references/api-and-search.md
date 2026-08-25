# gh api & gh search

## gh api — any REST/GraphQL endpoint

```bash
gh api user --jq .login                                  # who am I (active account)
gh api repos/{owner}/{repo}/releases                     # {owner}/{repo} filled from cwd repo or GH_REPO
gh api repos/{owner}/{repo}/issues/123/comments -f body='Hi from CLI'
gh api -X GET search/issues -f q='repo:cli/cli is:open'   # params as GET query string
gh api repos/{owner}/{repo}/rulesets --input payload.json # pre-built JSON body
gh api repos/{owner}/{repo}/issues --jq '.[].title'       # jq on response
```

Key flags:
- `-X/--method` — default GET, becomes POST when fields are added; override explicitly.
- `-f key=value` — raw string field. `-F key=value` — **typed** (`true`/`false`/`null`/int converted; `@file` or `@-` reads file/stdin).
- Nested payloads: `key[subkey]=value`; arrays: `key[]=v1 -F 'key[]=v2'`; empty array: `key[]`.
- `--paginate` — fetch all pages (REST auto; GraphQL requires `$endCursor` + `pageInfo{hasNextPage,endCursor}` in the query). Add `--slurp` to wrap pages into one outer JSON array.
- `-H header:value`, `-i` (include response headers), `--silent`, `--cache 1h`, `--hostname`, `--preview <name>`.
- GraphQL: `gh api graphql -f query='...' -F owner=...` — extra `-f/-F` become GraphQL variables.

## gh search — search across GitHub

Subcommands: `code`, `commits`, `issues`, `prs`, `repos`. Common flags: `-L/--limit N` (default 30), `--json/--jq/--template`, `-w` open in browser, qualifier flags like `--owner`, `--language`, `--label`.

```bash
# Repos
gh search repos cli shell --limit 10
gh search repos --owner=microsoft --language=go --good-first-issues=">=5" --json fullName,description,stargazersCount
gh search repos --topic=mcp --sort=stars --json fullName

# Issues / PRs
gh search issues --assignee=@me --state=open --json repository,number,title,url
gh search prs --review-requested=@me --state=open
gh search issues label:bug author:monalisa state:open     # raw qualifiers as args

# Code (legacy engine — no regex; may differ from github.com UI)
gh search code panic --repo cli/cli
gh search code lint --filename package.json --language=javascript

# Commits
gh search commits "bug fix" --author-name="Jane Doe"
gh search commits --committer=monalisa --author-date="<2022-02-01"
```

Gotchas:
- Exclusion qualifiers starting with `-` need `--`: `gh search issues -- "-label:bug"` (bash) or `gh --% search issues -- ...` (PowerShell).
- Semantic/hybrid ranking exists for issues only: `--search-type semantic|hybrid` (not on GHES; ignores `--sort`/`--order`).
- PR-specific filters: `--checks pending|success|failure`, `--draft`, `--merged`, `--review none|required|approved|changes_requested`, `--base/-B`, `--head/-H`.
- Repo numeric filters accept ranges: `--stars ">5000"`, `--size "<1000"` (KB).

Prefer `gh search` over hand-rolled `gh api /search/*` calls — it handles qualifiers and pagination for you.
