---
name: system-update
description: Use when the user asks to update/upgrade system packages and CLI tools — Homebrew, npm globals, Claude Code, Codex CLI, agy, pi, prime-agent, and ori. Runs them sequentially as a single chain and reports results.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: ""
  hermes_tags: system, update, upgrade, homebrew, npm, cli-tools, maintenance
  version: 1.2.0
---

# System Update

## Overview

Runs the full chain of system + tool updates on macOS in the correct order:

1. **`brew upgrade`** — upgrade all outdated Homebrew formulae and casks
2. **`npm update -g`** — update all globally-installed npm packages
3. **`claude update`** — update Claude Code CLI to latest
4. **`codex update`** — update Codex CLI to latest
5. **`agy update`** — update agy to latest
6. **`pi update --all`** — update pi itself AND all installed extensions/packages (verified: `--all` = pi self + extensions; do NOT use plain `pi update`, which is self-only and silently skips extensions)
7. **`prime-agent update`** — update prime-agent CLI to latest
8. **`ori update`** — update ori CLI to latest

## When to Use

- User asks to "update everything", "upgrade all tools", "run system updates"
- User explicitly names the chain (e.g., "brew upgrade and npm update")
- Periodic maintenance / housekeeping

**Don't use for:**
- Single-tool updates (just run that one command directly)
- Linux systems (this chain is macOS-specific due to Homebrew)

## How to Run

### Step 1 — Execute the update chain

Run all eight commands as a single sequential chain with `&&` so each step only runs if the previous one succeeded. Because `brew upgrade` can be slow, use **background mode** with notification:

```
terminal(
  command="brew upgrade && npm update -g && claude update && codex update && agy update && pi update --all && prime-agent update && ori update",
  background=true,
  notify_on_complete=true
)
```

### Step 2 — Retrieve and review output

Once the process completes (you'll be notified), read the full log:

```
process(action="log", session_id="<session_id>")
```

### Step 3 — Report a summary table

Present results in a clear table:

| # | Command | Result |
|---|---------|--------|
| 1 | `brew upgrade` | ✅ / ❌ + details |
| 2 | `npm update -g` | ✅ / ❌ + details |
| 3 | `claude update` | ✅ / ❌ + details |
| 4 | `codex update` | ✅ / ❌ + details |
| 5 | `agy update` | ✅ / ❌ + details |
| 6 | `pi update --all` | ✅ / ❌ + pi version + extensions updated |
| 7 | `prime-agent update` | ✅ / ❌ + version/details |
| 8 | `ori update` | ✅ / ❌ + version/details |

### Step 5 — Greedy cask follow-up (optional)

`brew upgrade` skips casks with `auto_updates true` or `version :latest` (e.g. Google Cloud SDK / `gcloud-cli`, some browsers). They stay outdated until forced. If the user wants them upgraded too, run after the main chain **in the background**:

```
terminal(command="brew upgrade --greedy", background=true, notify_on_complete=true)
```

`--greedy` is slower and can surface casks whose cleanup step needs `sudo` (see Pitfall #7). It also prints a "Some casks ... require `--greedy`" hint on every plain `brew upgrade` — that hint is the trigger to offer this step.

### Step 4 — Flag non-blocking warnings

Surface any warnings from the output that the user should know about:

- **Homebrew untrusted taps:** suggest `brew trust <tap>` or `brew untap <tap>`
- **npm allow-scripts:** list packages with blocked install scripts. The warning suggests `npm config set allow-scripts=...`, but that npm config key **only exists on npm 11+**. On npm 10.x (and earlier) it fails with `allow-scripts is not a valid npm option`. Use the one-shot flag instead: `npm install -g --allow-scripts=<pkg> <pkg>@<version>`. That reinstalls the package with its script allowed (no block warning).
- **Deprecated packages:** note any npm deprecation warnings
- **Claude Code duplicate installs:** when updates report multiple installations or a leftover npm global, surface a cleanup suggestion like `npm -g uninstall @anthropic-ai/claude-code`
- **Codex upgraded via Homebrew:** if `codex` is installed as a cask, `brew upgrade` may already have updated it. The standalone `codex update` in this chain will likely detect it is already current and ask only to restart Codex — this is expected, not a failure.
- **Formula import errors after `brew upgrade`:** if the upgrade log reports `formula requires at least a URL` for a tap formula, inspect the formula file directly. If it only defines a Linux/Intel URL and is missing a macOS/ARM section, you can remove the broken formula file so macOS resolves the command via the cask instead.
- **Untap dependency check:** before removing an untrusted tap, confirm no installed packages depend on it with `brew tap-info <tap>` and `brew list --versions`.
- **`brew doctor` PATH warning:** if `brew doctor` reports `/usr/bin` before `/opt/homebrew/bin`, recommend adding `export PATH="/opt/homebrew/bin:$PATH"` to `~/.zshrc`. Verify afterward with `echo $PATH`.

## Customizing the Chain

If the user wants to add or remove tools, adjust the `&&` chain accordingly. Common additions:

- `pipx upgrade --all` — Python CLI tools
- `rustup update` — Rust toolchain
- `hermes update` — Hermes Agent itself
- `gem update` — Ruby gems
- `mas upgrade` — Mac App Store apps (requires `mas`)

Only include tools that are actually installed — a missing command will fail the `&&` chain.

## Common Pitfalls

1. **Running in foreground blocks the session.** `brew upgrade` alone can take minutes. Always use `background=true` + `notify_on_complete=true`.

2. **A missing tool breaks the chain.** If the user doesn't have `codex` or `agy` installed, the `&&` chain stops at the first failure. Either skip missing tools or use `;` instead of `&&` to run all regardless of failures.

3. **Not reading the full log.** The poll output is truncated. Use `process(action="log")` to get the complete output before summarizing.

4. **Forgetting to flag warnings.** Untrusted taps and npm allow-scripts warnings are easy to miss in long output but matter for the user.

5. **Safe follow-up for untrusted taps.** Before untapping, confirm no installed dependencies need that tap. If safe, run `brew untap <tap>`. If the tap still contains installed packages, untap will refuse.

6. **Safe follow-up for malformed tap formulae.** `brew update` may not fix an invalid formula. If `brew doctor` / `brew info` still reports `formula requires at least a URL`, inspect the formula file directly. If it lacks a macOS/ARM URL, remove the file with sudo and let the generic cask handle macOS. If formula removal would break an installed dependency, report that instead and do not apt the tap.

7. **Non-interactive `sudo` wall on cask uninstall.** Some casks (e.g. `miniconda`) declare `uninstall delete: "#{caskroom_path}/base"`. Homebrew **always** escalates that `rm` to `sudo` even when the dir is fully user-owned — and the background shell can't supply a password, so the upgrade "fails" with `sudo: a terminal is required to read the password` even though the **new** version was already staged. Symptoms: `brew outdated --greedy` still lists the cask, `/opt/homebrew/bin/<tool>` is a dead symlink, and no working binary exists. Recovery **without the user's password** (full recipe in `references/cask-sudo-recovery.md`):
   1. Confirm the dir is user-owned with no root files and no data to lose: `find <prefix>/base -not -user "$(whoami)" | wc -l` and check for `base/envs`.
   2. Clear brew's stale metadata + dead symlink so the cask is treated as uninstalled: `rm -rf <caskroom>/<name>/.metadata <caskroom>/<name>/<oldver>` and `rm -f /opt/homebrew/bin/<tool>`.
   3. `brew install --cask <name>` — writes only to user-owned `/opt/homebrew/Caskroom` and links to user-owned `/opt/homebrew/bin`, so **no sudo**. If it bails on relinking ("latest version is already installed"), run the official `.sh` installer brew already downloaded into the same prefix, then recreate the symlink yourself.

8. **`pi update` approval prompt in background shells.** `pi` may prompt to trust project-local files (`--approve`), and an unanswered prompt hangs a background process forever. If the background log stalls at an approval question, kill the session and rerun as `pi update --all --approve` (or `--no-approve` to ignore project-local files).

9. **Non-registry packages in a global npm prefix.** `npm update -g` can fail with `E404` when a global package was installed from a private URL, standalone bundle, or source repository and is not published under its package name on the public npm registry (for example, `prime-agent`). Do not uninstall that package to make the bulk update pass. Inspect the active npm context with `command -v npm`, `npm prefix -g`, and `npm ls -g --depth=0 --json`; update registry-backed packages explicitly while excluding the non-registry package, then run that tool's own updater. On machines with multiple npm prefixes (such as `/opt/homebrew` and a user-local prefix), repeat the inspection for the npm executable that the failing shell actually resolves.

## References

- `references/cask-sudo-recovery.md` — step-by-step recovery for the non-interactive `sudo` cask-uninstall wall (miniconda-style), verified end-to-end.

## Verification Checklist

- [ ] All eight (or customized) commands executed without fatal errors
- [ ] Full output retrieved via `process(action="log")`
- [ ] Summary table presented to user
- [ ] Non-blocking warnings surfaced and explained
- [ ] If requested, follow-up cleanup applied safely: untrusted taps checked for dependencies before untapping; malformed tap formulae inspected and only removed when safe
- [ ] If `brew doctor` was run afterward, PATH feedback provided if `/usr/bin` precedes `/opt/homebrew/bin`
- [ ] If `--greedy` was run: cask `sudo` wall handled per `references/cask-sudo-recovery.md` if a cask upgrade failed on `sudo: a terminal is required`; final `brew outdated --greedy` empty
- [ ] npm allow-scripts issue fixed via one-shot `--allow-scripts=` flag (NOT `npm config set`, which fails on npm <11)
