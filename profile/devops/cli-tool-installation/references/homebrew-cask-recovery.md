# Homebrew cask recovery for non-interactive shells

Use this when a Homebrew cask upgrade/install stages a new payload but aborts during cleanup or relinking because the shell cannot answer a `sudo` prompt.

## Symptom pattern

Typical output includes one or more of:

- `sudo: a terminal is required to read the password`
- `sudo: a password is required`
- `Failure while executing; /usr/bin/sudo ... /bin/rm ... exited with 1`
- `Warning: Not upgrading <name>, the latest version is already installed`
- The cask's binary symlink exists but points at a missing `base` directory, or the `base` directory is incomplete

## Safe check first

Before deleting anything, confirm the cask's current data tree is not carrying user data you care about.

```bash
find /opt/homebrew/Caskroom/<name>/base -not -user "$(whoami)" 2>/dev/null | wc -l
ls /opt/homebrew/Caskroom/<name>/base/envs 2>/dev/null || echo "no envs"
```

If the tree contains important envs or non-user-owned files, stop and assess manually.

## Recovery path

### 1) Remove stale metadata and dead symlinks

```bash
rm -f /opt/homebrew/bin/<tool>
rm -rf /opt/homebrew/Caskroom/<name>/.metadata /opt/homebrew/Caskroom/<name>/<oldver>
```

### 2) Reinstall the cask

```bash
brew install --cask <name>
```

### 3) If the installer says the target already exists

Some installers refuse to unpack into an existing `base` directory even after Homebrew metadata was cleared.

```bash
rm -rf /opt/homebrew/Caskroom/<name>/base
brew install --cask <name>
```

### 4) If Homebrew skips relinking but the downloaded installer is present

Run the staged installer directly into the same prefix, then recreate the symlink if needed.

```bash
SH=$(find /opt/homebrew/Caskroom/<name>/<newver> -name '*.sh' | head -1)
bash "$SH" -b -f -p /opt/homebrew/Caskroom/<name>/base
ln -sf /opt/homebrew/Caskroom/<name>/base/condabin/<tool> /opt/homebrew/bin/<tool>
```

## Verify

```bash
<tool> --version
brew outdated --greedy
```

The cask is recovered when the command runs and `brew outdated --greedy` is clean.
