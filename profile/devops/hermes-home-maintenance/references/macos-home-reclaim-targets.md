# macOS Home Reclaim Targets (field-tested)

Sizes observed 2026-08-25 on the user's Mac (post-cleanup audit); the commands and
classification rules are the durable part, sizes are indicative only.

## High-yield rebuildable caches (rm-safe after open-handle check)

| Target | Typical size | Notes |
|---|---|---|
| `~/.cache/codex-runtimes/codex-runtime-install-*` | 0.3–1.9 GB each | Stale temp dirs left by Codex runtime updates. `stat -f "%Sm %N"` them; always keep newest `codex-primary-runtime`, rm the rest. |
| `~/.npm/_cacache` | 3 GB+ | `npm cache clean --force`. |
| `~/.cache/puppeteer/` | ~1.3 GB | Downloaded Chrome/Firefox binaries; re-fetched on demand. |
| `~/.local/share/claude/versions/<old>` | ~325 MB per build | Run `claude --version` FIRST; keep active build, delete older only. |
| Go module cache | varies | `go clean -modcache`. |
| Homebrew downloads/prunable kegs | ~100 MB+ | `brew cleanup`. |
| `~/Library/Caches/@*-updater`, `electron` | 100–450 MB | App updater/electron download caches; skip if an open handle exists. |
| `~/.hermes/state.db.pre-update-emergency-*.bak` | ~176 MB each | Keep only the newest as rollback. |
| `uv` unused Python installs | ~45 MB each | `uv python uninstall <ver>` — see guard rails below. |
| Stray `.DS_Store`, `*.pyc`, `__pycache__`, stale `.zcompdump*`, dead `*.log`/`*.bak`/`*.orig` | 50–250 MB bulk | Sweep with venv/node_modules/Library/Movies pruned; skip files open in /tmp/lsof_all.txt. |

A full pass on this machine reclaimed ~13 GiB (29.4 → 42.8 GiB free).

## Ask-first tier (personal data/config — MOVE to Trash, don't rm)

Move to `~/.Trash/<name>.<YYYYMMDD>` so it stays recoverable until Trash is emptied:

- `~/.<tool>.backup-*/` snapshots — may contain `auth.json` and tokens.
- Possibly-abandoned tool data trees (e.g. an old app's bundled conda env).
- Loose scratch outputs sitting in `~` root (one-off scripts, generated md/svg/html).
- Old files in `~/Downloads`.

## Guard rails

- Global lsof snapshot once per session (`lsof -wn > /tmp/lsof_all.txt`); grep every
  candidate before rm/mv. Gateway logs and Chrome cache journals WILL show up open.
- Never candidates: `~/Library/Application Support/Google/Chrome` (browser profile
  DATA, tens of GB), `~/Movies/TV` libraries, OneDrive symlinks, active tool state,
  and any model/store the user carved out explicitly (e.g. Ollama GGUF blobs).
- `uv` Python uninstalls: grep `requires-python` / `.python-version` across project
  dirs AND check an existing `.venv/bin/python --version`; a `>=3.8` pin with only a
  3.12 venv does not protect 3.8 — absence of any 3.8 venv clears it.
- Verification per phase: `df -k /` free-bytes delta, `--version` health checks for
  touched tools (hermes/claude/codex/go/ollama), confirm kept items intact.
