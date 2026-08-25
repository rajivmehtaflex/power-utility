# Whole-Home (`~`) Disk Audit — Patterns & macOS Path Classifications

Proven recipes from a full-home audit on a macOS dev machine (~12 GB green-tier + ~4 GB yellow-tier identified). Complements the `~/.hermes`-focused workflow in SKILL.md; same core/classify/verify/report discipline applies to the entire home directory.

## Inventory recipe (run in this order)

1. **Dotfile dirs by size** — the fastest map of where the bytes live:
   ```bash
   du -sh ~/.[a-zA-Z]* 2>/dev/null | sort -rh | head -40
   ```
2. **Junk-file sweep** — prune `~/Library` and `node_modules` first or the output drowns. Note quoting: leave `~/Library` unquoted so the shell expands it; quote `"*/node_modules"` so find gets the glob:
   ```bash
   find ~ -maxdepth 4 \( -path ~/Library -o -path "*/node_modules" \) -prune -o \
     -type f \( -name ".DS_Store" -o -name "*.pyc" -o -name "*.log" -o -name ".zcompdump*" \
     -o -name "*.bak" -o -name "*.orig" \) -print
   ```
   Summarize by extension with awk instead of dumping hundreds of paths.
3. **User folders**: `du -sh ~/Downloads ~/Desktop ~/Documents ~/go ~/agent-skills ...`
4. **Drill into whatever tops the list**: `~/.cache/*`, `~/Library/Caches/*`, `~/.local/share/*`, `~/.codex/*`, `~/.ollama/*`.
5. **Check timestamps before judging anything stale**: `stat -f "%Sm %N"` (or `ls -lat`). A huge dir touched today is in use; the same dir untouched for weeks is a candidate.

## Known-path classification (macOS dev machine)

| Path | Class | Notes |
|---|---|---|
| `~/.cache/codex-runtimes/codex-runtime-install-*` | delete | Leftover temp install dirs from runtime updates; `codex-primary-runtime` is the live one — keep it |
| `~/.npm/_cacache` | delete | Download cache, often multi-GB; rebuilt on demand |
| `~/.cache/{puppeteer,uv,chrome-devtools-mcp,node,selenium}` | delete ok | Re-fetched/rebuilt when next needed |
| `~/Library/Caches/<app>-updater`, `electron`, `Google` | delete ok | App-updater and browser caches, rebuildable |
| `~/Library/Caches/Homebrew` | delete | `brew cleanup` |
| `~/.local/share/claude/versions/*` | keep newest only | Each build is ~300 MB; confirm the active one with `<tool> --version` before pruning siblings |
| `~/.hermes/state.db.pre-update-emergency-*.bak` | keep newest 1 | Rollback insurance; older generations deletable |
| `~/go/pkg/mod` | delete ok | `go clean -modcache`; re-downloaded by builds |
| `~/.<tool>.backup-<timestamp>/` dirs | ASK FIRST | Full config snapshots; frequently contain `auth.json`/tokens |
| `~/.ollama/models` | ASK FIRST | Check against the user's stated workflow (e.g. if Ollama is excluded, the pull may be droppable) |
| App-data homes (`.claude-science`, `.prime`, …) | ASK FIRST | May bundle conda envs, encryption keys, auth |
| `~/.local/share/uv/python/cpython-X.Y` | CHECK FIRST | Run `uv python list --only-installed`; only remove versions nothing pins |
| Loose scratch files in `~` root (old `.md`/`.py`/`.svg` outputs) | ASK FIRST | List individually with dates; tiny but visible clutter |
| `~/Library/Application Support/Google/Chrome` | NEVER flag | Browser profile / user data, not junk — can legitimately be 15–20 GB |
| `.ssh`, `.aws`, `.kube`, `.config`, `.docker`, live tool state dirs | KEEP | Credentials and configuration |

Versioned-tool rule of thumb: wherever a tool keeps self-contained builds (`versions/`, dated install dirs), the newest timestamp wins and older siblings are green-tier — but verify the active binary/version first.

## Report format (landed well)

Three tiers, emoji headers, always with a **Size** column and total reclaim estimate:

- 🟢 **Safe to delete now** — rebuildable caches, superseded versions/backups, junk files. One row each with reason.
- 🟡 **Ask first** — backups containing secrets, model weights, app data, old scratch/Downloads files listed individually with dates and a concrete question each.
- 🔴 **Keep** — config/auth/state and project folders. Explicitly call out big-but-legitimate paths (e.g. the Chrome profile) so they aren't mistaken for overlooked candidates.

Never delete anything until the user picks a tier. When executing, offer phased deletion with before/after `du` accounting (same discipline as the `~/.hermes` workflow in SKILL.md).
