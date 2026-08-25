# Cask sudo-recovery (non-interactive shell)

## Problem
A Homebrew cask declares `uninstall delete: "#{caskroom_path}/base"` (miniconda does this).
Homebrew **always** escalates that `rm` to `sudo`, even when the directory is fully
user-owned. In the agent's non-interactive background shell there is no password prompt,
so the step fails with:

```
sudo: a terminal is required to read the password
sudo: a password is required
Error: <cask>: Failure while executing; `/usr/bin/sudo -E -- /usr/bin/xargs ...` exited with 1
```

Even though the **new** version was already downloaded/staged, the upgrade aborts. Result:
- `brew outdated --greedy` still lists the cask.
- `/opt/homebrew/bin/<tool>` is a **dead symlink** (old `base` gone).
- No runnable binary exists → tool is broken.

Do NOT ask the user for their sudo password. There is a passwordless recovery.

## Verify it is safe first
```bash
# 0 root-owned files?
find /opt/homebrew/Caskroom/<name>/base -not -user "$(whoami)" 2>/dev/null | wc -l
# any conda/pip envs to lose?
ls /opt/homebrew/Caskroom/<name>/base/envs 2>/dev/null || echo "no envs"
```
If both are clean (0 root files, no envs), proceed. If the dir has envs the user cares
about, stop and ask before removing it.

## Recovery (no sudo)
```bash
# 1. remove dead symlink + stale brew metadata so brew treats the cask as UNinstalled
rm -f /opt/homebrew/bin/<tool>
rm -rf /opt/homebrew/Caskroom/<name>/.metadata /opt/homebrew/Caskroom/<name>/<oldver>

# 2. fresh install writes only to user-owned Caskroom + links to user-owned /opt/homebrew/bin
brew install --cask <name>
```
That usually relinks and finishes. If brew instead prints
`Warning: Not upgrading <name>, the latest version is already installed` and the symlink
is STILL missing / `base` is incomplete (no `bin/<tool>`, no `condabin/<tool>`):

```bash
# 3. run the official installer brew already downloaded, into the SAME prefix
SH=$(find /opt/homebrew/Caskroom/<name>/<newver> -name '*.sh' | head -1)
rm -rf /opt/homebrew/Caskroom/<name>/base
bash "$SH" -b -f -p /opt/homebrew/Caskroom/<name>/base
# (run in background if it times out at 60s — the .sh payload unpack is slow)

# 4. recreate the symlink brew skipped
ln -sf /opt/homebrew/Caskroom/<name>/base/condabin/<tool> /opt/homebrew/bin/<tool>
```

## Verify
```bash
<tool> --version
brew list --cask <name>        # should list a *.rb
brew outdated --greedy         # should be empty
```

## Real example (this session)
- `brew upgrade --greedy` -> `gcloud-cli` 567.0.0->575.0.1 ok; `miniconda` failed on sudo wall.
- `rm -rf base` then `brew reinstall`/`brew install` still hit sudo (brew re-escalates on any
  `uninstall delete:` path).
- Cleared metadata + dead symlink -> `brew install --cask miniconda` staged `py314` but bailed on
  relink. Ran `Miniconda3-py314_26.5.3-1-MacOSX-arm64.sh -b -f -p .../base`, recreated symlink.
- Final: `conda --version` -> 26.5.3; `brew outdated --greedy` empty. OK
