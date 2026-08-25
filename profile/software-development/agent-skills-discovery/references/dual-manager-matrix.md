# Dual-Manager Matrix — npx skills vs gh skill

Verified 24/08/2026 via Exa + `gh --version 2.98.0` + `gh skill --help`.

## Verb mapping

| Task | `npx skills add` (Vercel/skills.sh) | `gh skill` (GitHub CLI v2.90+, preview) |
|---|---|---|
| Search | — (use Exa or `gh skill search`) | `gh skill search <keyword>` |
| Preview | `npx skills add owner/repo --list` (names only) | `gh skill preview owner/repo [skill]` (full SKILL.md) |
| Install | `npx skills add owner/repo [--skill name] [--agent <agent>] [--global] [--copy]` | `gh skill install owner/repo [skill[@tag]] [--agent <a>] [--scope user|project]` |
| List installed | `npx skills list` (skills.sh) / `hermes skills list` | `gh skill list [--agent <a>] [--scope <s>]` |
| Update | re-run `npx skills add` | `gh skill update [--all] [skill]` |
| Publish/validate | — | `gh skill publish --dry-run` |

## Worked examples

### RunPod (official vs legacy)
- Official: `runpod/runpod-plugins-official` — 1 plugin, 6 skills (`runpod` router, `runpod-mcp`, `runpodctl`, `flash`, `companion-clis`, `runpod-usage`). Source: `docs.runpod.io/get-started/agent-skills` + GitHub README skill table.
- Legacy: `runpod/skills` — 2 skills (`runpodctl`, `flash`).

```bash
# Preferred (works with any agent)
npx skills add runpod/runpod-plugins-official       # all 6
npx skills add runpod/runpod-plugins-official --skill runpodctl  # one lane
# gh alternative (same spec)
gh skill install runpod/runpod-plugins-official
gh skill preview runpod/runpod-plugins-official       # inspect first
```

Dependency: `curl -sSL https://cli.runpod.net | bash` or `brew install runpod/runpodctl/runpodctl`, then `export RUNPOD_API_KEY=<key>` and `runpodctl doctor`.

### gh CLI lean guides (official)
- Repo `cli/cli` ships `skills/gh/SKILL.md` (gh pain points: `--json`/`--jq`/`--template`, pagination `-L`/`--paginate`, `--repo` targeting, `gh search` vs `list`) and `skills/gh-skill/SKILL.md` (self-management).
```bash
gh skill preview cli/cli gh          # read lean guide
gh skill install cli/cli gh
gh skill install cli/cli gh-skill
```

## When to choose which

- Already authenticated with `gh` and need search/preview/pinning → `gh skill`.
- Need auto-detection across 50+ agents or working without `gh` → `npx skills add`.
- Both write to spec-compliant `SKILL.md` locations; they are interoperable.
