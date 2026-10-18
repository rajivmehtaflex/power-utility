---
name: system-update
description: "Use when the user asks to update/upgrade system packages and CLI tools — Homebrew, npm globals, Claude Code, Codex CLI, agy, pi, and ori. Runs them sequentially as a single chain and reports results."
license: MIT
metadata:
  author: Hermes Agent
  version: 1.3.0
  hermes:
    tags: [system, update, upgrade, homebrew, npm, cli-tools, maintenance]
    related_skills: []
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
7. **`ori update`** — update ori CLI to latest

## When to Use

- User asks to "update everything", "upgrade all tools", "run system updates"
- User explicitly names the chain (e.g., "brew upgrade and npm update")
- Periodic maintenance / housekeeping

**Don't use for:**
- Single-tool updates (just run that one command directly)
- Linux systems (this chain is macOS-specific due to Homebrew)

## How to Run

### Step 1 — Execute the update chain

Run all seven commands as a single sequential chain with `&&` so each step only runs if the previous one succeeded. Because `brew upgrade` can be slow, use **background mode** with notification:

> **Caution:** If any global npm package is non-registry (installed from a private URL, standalone bundle, or source repository and not published on the public npm registry), `npm update -g` will E404 and abort the entire `&&` chain — later steps never run. See Step 3 below for the two-phase recovery.

```
terminal(
  command="brew upgrade && npm update -g && claude update && codex update && agy update && pi update --all && ori update",
  background=true,
  notify_on_complete=true
)
```

> **Login-shell npm vs foreground npm:** On macOS with a shadowing Homebrew node, a background `terminal(background=true)` is a login shell. Verify which npm it resolves: `zsh -lic 'command -v npm; npm prefix -g'`. Login shells often resolve `/opt/homebrew/bin/npm` with prefix `/opt/homebrew`, while interactive non-login shells resolve `~/.local/bin/npm` with prefix `~/.local`. If the prefixes differ, a bare `npm update -g` may E404 on a package that exists only in the other prefix. Always inspect both prefixes with their absolute npm paths before summarizing registry failures.

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
| 7 | `ori update` | ✅ / ❌ + version/details |
| 8 | `brew cleanup` | ✅ stale downloads and old Cellar versions reclaimed |

### Step 4 — Recover from npm E404 mid-chain

Because step 2 (`npm update -g`) runs inside the `&&` chain, a single non-registry package (see Pitfall #9) aborts the **entire** chain — steps 3–8 never execute. If the background log shows an `npm error code E404`, do **not** restart the full chain. Instead, switch to a two-phase recovery:

**Phase A — Update only registry-backed globals:**
1. `zsh -lic 'command -v npm; npm prefix -g'` — confirm which npm the background shell used.
2. `npm ls -g --depth=0` — list globals and note the active prefix root.
3. `npm prefix -g` — confirm the active prefix.
4. Inspect each global in *each* npm prefix: `cat <global-root>/<pkg>/package.json | grep '"version"'` and `npm view <pkg> version`.
5. Update each registry-backed package by **explicit name** (omitting the non-registry one):
   `npm update -g <pkg1> <pkg2> ...` or `npm install -g <pkg>@latest`.
6. Smoke-test each updated binary via the PATH winner: `command -v <tool>` first, then `<tool> --version` — the PATH winner may be the `~/.local` copy in a different prefix, not the one just updated.
7. If the non-registry package's PATH binary is a symlink into a standalone install (`readlink -f /opt/homebrew/bin/<tool>` → `~/.local/share/<tool>/releases/...`), the npm global is a stale duplicate. Remove it with `npm uninstall -g <pkg>`, recreate the `/opt/homebrew/bin/<tool>` symlink to the standalone binary, and verify — this makes `npm update -g` exit 0 permanently instead of E404 on every future run. Full recipe in `references/standalone-install-duplicates.md`.

**Phase B — Run non-registry tool updaters individually:**
Run `claude update`, `codex update`, `agy update`, `pi update --all --no-approve` (use `--approve` only when project-local resources are trusted), and `ori update` as **separate commands** (not an `&&` chain) so a failure in one doesn't block the rest. Each tool's updater already handles its own "already up to date" logic.

> **Decision tip:** If you anticipate non-registry globals, split the workflow after Homebrew: run `brew upgrade` first, then explicit-name registry-only npm updates for every active prefix, then each CLI updater individually. Avoid a bare `npm update -g` and a single `&&` chain in this case; a non-registry package can abort npm's step and prevent later tools from updating.

### Step 5 — Greedy cask follow-up (optional)

`brew upgrade` skips casks with `auto_updates true` or `version :latest` (e.g. Google Cloud SDK / `gcloud-cli`, some browsers). They stay outdated until forced. If the user wants them upgraded too, run after the main chain **in the background**:

```
terminal(command="brew upgrade --greedy", background=true, notify_on_complete=true)
```

`--greedy` is slower and can surface casks whose cleanup step needs `sudo` (see Pitfall #7). Do not rely on the "Some casks ... require `--greedy`" hint as the trigger — a plain `brew upgrade` can omit it even when a cask is still outdated (`gcloud-cli` is a recurring example). Check `brew outdated --greedy` directly; if it lists anything, offer this step.

### Step 6 — Post-chain cleanup with `brew cleanup`

After the chain completes, run `brew cleanup` to remove stale downloads, old versions of upgraded formulae, and stale lock files. `brew upgrade` leaves previous versions in the Cellar; `brew cleanup` reclaims that disk space. Casks are covered by the same command — there is **no** `--cask` flag (`brew cleanup --cask` errors out).

```
terminal(command="brew cleanup", background=true, notify_on_complete=true)
```

### Step 7 — Flag non-blocking warnings

Surface any warnings from the output that the user should know about:

- **Homebrew untrusted taps:** suggest `brew trust <tap>` or `brew untap <tap>`
- **npm allow-scripts:** list packages with blocked install scripts. The warning suggests `npm config set allow-scripts=...`, but that npm config key **only exists on npm 11+**. On npm 10.x (and earlier) it fails with `allow-scripts is not a valid npm option`. Use the one-shot flag instead: `npm install -g --allow-scripts=<pkg> <pkg>@<version>`. That reinstalls the package with its script allowed (no block warning). **Verify before fixing**: native modules that ship bundled prebuilds (e.g. `koffi`, `zeromq` — check for `darwin_arm64`/`arm64` dirs under `build/` or `prebuilds/` in the nested `node_modules`) work fine with the script blocked, so the warning is noise. Smoke-test the owning tool (`<tool> --help` exits 0) and only use the one-shot flag if it is actually broken.
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

8. **`pi update` approval prompt in background shells.** `pi` may prompt to trust project-local files (`--approve`), and an unanswered prompt hangs a background process forever. If the background log stalls at an approval question, kill the session and rerun as `pi update --all --approve` (or `--no-approve` to ignore project-local files). `pi update --all` can also report "already up to date" while a newer version is pending approval; running with `--approve` unblocks the actual upgrade.

9. **Non-registry packages in a global npm prefix.** `npm update -g` can fail with `E404` when a global package was installed from a private URL, standalone bundle, or source repository and is not published under its package name on the public npm registry (for example, a git-installed package; `npm view <pkg>` 404s). Do not uninstall it when the npm global is the working install. If the PATH binary is a symlink into a standalone install (`~/.local/share/<tool>/releases/...`), the npm global is a stale duplicate — uninstalling it is the correct permanent fix (Step 4, `references/standalone-install-duplicates.md`). **Verified recovery recipe:**
   1. Find all globals: `npm ls -g --depth=0` (note the prefix root it prints — may differ from `npm prefix -g` if prefixes changed mid-history).
   2. For each registry-backed package, compare `npm view <pkg> version` against the installed version (read `<global-root>/<pkg>/package.json` directly — `require()` can fail on packages with restrictive `exports`).
   3. `npm update -g <pkg1> <pkg2> ...` (explicit list, excluding the non-registry one) — but this only stays in-range; for globally pinned packages it usually does little.
   4. `npm install -g <pkg>@latest` for anything still behind.
   5. Re-verify via the actual binaries (`<tool> --version`), not the package.json on disk.
   **Watch for dual prefixes:** installs land in the *current* `npm prefix -g` (e.g. `~/.local`), while stale older copies may remain under a previous prefix (e.g. `/opt/homebrew/lib/node_modules`). The shadowing `~/.local/bin` wins on PATH, so on-disk versions under the old prefix can look stale while `--version` already reports the new one — that is not a failure. On machines with multiple npm prefixes, repeat the inspection for the npm executable that the failing shell actually resolves.
   **After `brew upgrade` upgrades node**, re-verify which npm the background shell resolves (`zsh -lic 'command -v npm; npm prefix -g'`). `brew upgrade` can relink `/opt/homebrew/bin/npm` and `npx` to formula-managed launchers and change the active npm version and prefix. Record `/opt/homebrew/bin/npm --version` before and after; if the active npm is Homebrew-managed, do not upgrade it separately with `npm install -g npm@latest` — report the before/after versions as a deliberate Homebrew-managed skip.

10. **Login-shell npm resolution differs from interactive shell.** `terminal(background=true)` starts a login shell. Verify with `zsh -lic 'command -v npm; npm prefix -g'`. If `~/.local/bin` shadows `/opt/homebrew/bin`, login shells may resolve `/opt/homebrew/bin/npm` with prefix `/opt/homebrew`, while non-login shells resolve `~/.local/bin/npm`. Different prefixes hold different globals, so a bare `npm update -g` may E404 on a package present only in the other prefix. Inspect and update each prefix with its own absolute npm path.

## Additional verification pitfalls

- Check npm resolution inside the background shell itself, not only the foreground terminal: login-shell startup can change PATH and select `/opt/homebrew/bin/npm` instead of `~/.local/bin/npm`. Use absolute npm paths during recovery and inspect both prefixes; verify PATH-winning binaries afterward.
- Recheck shadowing local installs after updating a second prefix. An explicit `npm update -g` can leave a pinned local package unchanged; use `npm install -g <package>@latest` for a verified lagging package, then check its actual binary.
- Read a package's `bin` manifest before smoke-testing unfamiliar globals. Do not guess a command with `npm exec`, which can attempt registry installation. `mcphub-gateway --help` starts its network connection rather than displaying help, so use manifest/version inspection unless intentionally testing that endpoint.
- **Which npm a login shell resolves (macOS dual-prefix trap).** Verify with `zsh -lic 'command -v npm; npm prefix -g'`. On a machine where `~/.local/bin` shadows `/opt/homebrew/bin`, a **login** shell (which is what `terminal(background=true)` gives you) resolves `npm` to `/opt/homebrew/bin/npm` with prefix `/opt/homebrew`, while a **non-login** shell resolves `~/.local/bin/npm`. Different prefixes hold different globals, so a bare `npm update -g` may E404 on a package that the other prefix's `npm ls -g` never shows. Inspect and update **each prefix with its own absolute npm path**.
- **`~/.local/bin/npm` may be a symlink into another tool's bundled Node runtime.** Check with `ls -l` / `os.path.realpath`. If it points at e.g. `~/.hermes/node/bin/npm`, that npm belongs to that tool — never `npm install -g npm@latest` into that prefix. It fails `EEXIST: file already exists` (the `~/.local/bin/npm` symlink is not npm's to overwrite), and forcing it would clobber the owning tool's runtime. Before upgrading Homebrew Node, record `/opt/homebrew/bin/npm --version`; afterward recheck its symlink target, version, and prefix because `brew upgrade` can relink `/opt/homebrew/bin/npm` and `npx` to the formula-managed launchers and change the active npm version. If the active npm is Homebrew-managed, do not restore or upgrade it separately with `npm install -g npm@latest`; report the before/after versions and `npm view npm version` as a deliberate Homebrew-managed skip.
- **A global can be installed in both prefixes; the stale copy is the one on PATH.** Enumerate both roots (`find <root> -maxdepth 3 -name package.json -not -path '*/node_modules/*/node_modules/*'`) and update both. A first `npm install -g <pkg>@latest` can report success (`added 73 packages`) yet leave the top-level `package.json` at the old version — so always re-read `<root>/<pkg>/package.json` and run `<tool> --version` on the PATH winner rather than trusting npm's exit code.

- **Native module major jump without prebuilds — skip it.** When a global npm package is a native module and the target version ships no prebuilds for this arch, skip the update rather than jumping a major version. The install script compiles the native binding from source; with install scripts blocked (the default) or `--ignore-scripts`, the package reports installed but its binary won't load. Check `<global-root>/<pkg>/prebuilds/` and `npm view <pkg>@<version> prebuilds` before updating a native module past its first version segment.
- **Do not run a bare `npm update -g` just to confirm the E404 is gone.** It updates every global in range, including npm itself when npm lives in the Homebrew node tree (npm 11→12 jump) and native modules you deliberately skipped (e.g. koffi 2→3). Verify recovery with `npm ls -g --depth=0` plus explicit-name updates, then smoke-test. If the bare update already ran, report the npm/native before-after honestly and load-test the native module with `node -e "require('<global-root>/<pkg>')"` instead of trusting package.json.

## References

- `references/cask-sudo-recovery.md` — step-by-step recovery for the non-interactive `sudo` cask-uninstall wall (miniconda-style), verified end-to-end.
- `references/update-autostash-cleanup.md` — clean up leftover hermes-update autostash entries in the Hermes git repo (back up, verify, drop).
- `references/standalone-install-duplicates.md` — reconcile standalone-installer CLIs with stale npm globals; removes the recurring E404 permanently.

## Verification Checklist

- [ ] All eight (or customized) commands executed without fatal errors
- [ ] Full output retrieved via `process(action="log")`
- [ ] Summary table presented to user
- [ ] Non-blocking warnings surfaced and explained
- [ ] If requested, follow-up cleanup applied safely: untrusted taps checked for dependencies before untapping; malformed tap formulae inspected and only removed when safe
- [ ] If `brew doctor` was run afterward, PATH feedback provided if `/usr/bin` precedes `/opt/homebrew/bin`
- [ ] If `--greedy` was run: cask `sudo` wall handled per `references/cask-sudo-recovery.md` if a cask upgrade failed on `sudo: a terminal is required`; final `brew outdated --greedy` empty
- [ ] npm allow-scripts issue fixed via one-shot `--allow-scripts=` flag (NOT `npm config set`, which fails on npm <11)
- [ ] `brew cleanup` run after the chain to reclaim disk space from old Cellar versions and stale downloads
