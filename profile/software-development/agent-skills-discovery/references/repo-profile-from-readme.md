# Deriving GitHub Repo About Fields From README.md

Pattern used 24/08/2026 for `rajivmehtaflex/graph-flow` — description was empty after creation, derived from README opening summary.

## Check current state

```bash
gh repo view owner/repo --json name,description,url,primaryLanguage,stargazerCount,updatedAt --jq .
gh api repos/owner/repo --jq '{description, homepage, topics}'
gh auth status   # verify Active account == repo owner (multi-account pitfall: 4 gh accounts)
```

## Set description + homepage + topics atomically

GitHub About description limit is 350 chars; aim for 100-160 for display.

```bash
gh repo edit owner/repo \
  --description "Portable Agent Skill for durable, stateful graph-based repo coordination — parallel work, conditional routing, bounded verify/repair loops, restart recovery & human approval gates." \
  --homepage "https://skills.sh/owner/repo" \
  --add-topic graph --add-topic agent-skill --add-topic orchestration \
  --add-topic state-machine --add-topic durable-execution
# Homepage shorthand: -h "https://skills.sh/owner/repo"
```

Single-field alternative:
```bash
gh repo edit owner/repo --description "Short one-line summary from README first paragraph."
gh repo edit owner/repo -h "https://skills.sh/owner/repo"
```

## Verify (source of truth)

```bash
gh api repos/owner/repo --jq '{description, homepage, topics, html_url}'
# Topics are set via --add-topic / --remove-topic (comma-separated for legacy flag, but new CLI accepts repeated --add-topic)
```

## Pitfalls

- Running from workspace root (`/Users/.../Dev`) infers wrong repo from `cwd` remotes — always pass explicit `owner/repo` when not inside the target repo.
- Empty description after `gh repo create` is normal — README is not auto-synced to About.
- Homepage must be a valid URL; use `skills.sh` canonical URL or docs site.
- Topics: `gh api` returns `topics: []` until set; `gh repo view --json repositoryTopics` shows same.

## Example derivation (graph-flow README)

README opening: "Graph Flow is a portable Agent Skill for coordinating repository work as a durable, stateful graph. It is useful when work needs parallel units, conditional routing, independent verification, bounded repair loops, restart recovery, or an explicit human approval gate."

Condensed to: "Portable Agent Skill for durable, stateful graph-based repo coordination — parallel work, conditional routing, bounded verify/repair loops, restart recovery & human approval gates." (152 chars)
