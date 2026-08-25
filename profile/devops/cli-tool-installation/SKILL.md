---
name: cli-tool-installation
description: Install, verify, and expose command-line tools on the user's machine, including PATH setup, shell reloads, and user-local installs from brew, pipx, pip --user, and uv.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: system-update
  hermes_tags: cli, install, path, shell, brew, pipx, uv, python, user-local
  platforms: macos, linux
  version: 1.0.0
---

# CLI Tool Installation

Use this skill when installing or exposing a command-line tool on the user's machine and you need the command to work in an interactive shell, not just in the current agent process.

## Goals

- Install a CLI tool cleanly
- Verify the executable is reachable from the user's shell
- Fix PATH exposure for user-local installs when needed
- Tell the user exactly how to refresh their shell session

## Recommended Workflow

### 1) Identify the install path used by the package manager

Common patterns:

- `brew install <tool>` → usually lands in Homebrew's bin directory
- `pipx install <tool>` → usually exposes shims in `~/.local/bin`
- `pip install --user <tool>` → usually exposes scripts in the user Python bin dir
- `uv tool install <tool>` → typically creates a shim in `~/.local/bin`

### 2) Verify from the same shell that performed the install

Always check with the actual command first:

```bash
command -v <tool>
<tool> --version
```

If the binary exists but isn't on PATH for interactive shells, don't assume the install failed.

### 3) Refresh the shell environment

If the user is in zsh or bash, prefer one of these after changing startup files:

```bash
source ~/.zshrc
# or
exec zsh
# or, for a login-shell change
source ~/.zprofile
```

### 4) Add only the missing bin directory, not a custom wrapper

If a user-local install is not visible, add the directory that actually contains the generated script to PATH in the appropriate shell init file.

Common examples:

- `~/.local/bin`
- `~/Library/Python/<major.minor>/bin`
- `~/.cargo/bin`
- `~/Library/Python/<major.minor>/bin`

Prefer putting persistent PATH edits in the user's shell startup files rather than exporting them only in the current agent session.

### 5) Re-verify in a fresh shell

After updating shell init files, verify the command in a fresh interactive shell, not only in the current terminal process:

```bash
zsh -ic 'command -v <tool> && <tool> --version'
```

## Remote Bootstrap and Current-Directory Launchers

For a remote Linux bootstrap delivered with `curl | bash`, distinguish three separate concerns:

1. **Download endpoint:** verify the current vendor URL and architecture mapping; do not copy stale documentation URLs blindly.
2. **Placement:** `curl | bash` runs a child shell. An exported `PATH` disappears when that child exits. If the user's required postcondition is an exact relative command such as `./code tunnel`, install the verified executable atomically at `"$PWD/code"`, not only in `~/.local/bin` or `/usr/local/bin`.
3. **Runtime verification:** verify the exact target path with `--version` and the required subcommand/help before reporting success. Print the exact command the user should run from the same directory.

Use a temporary download/extraction directory, verify the archive contents, install to a temporary file beside the target, and `mv` it into place. Refuse a target directory and fail clearly when the current directory is not writable. Keep interactive account authentication (for example, VS Code tunnel login) as the final user-driven step rather than attempting to automate credentials.

For Gist-backed bootstrap scripts, switch and verify the requested `gh` account before publishing, then fetch the raw Gist after `gh gist edit`, run syntax/lint checks on the fetched file, and compare it byte-for-byte with the tested local file. Prefer a stable raw URL for users; immutable revision URLs remain on older code.

See `references/remote-bootstrap-and-local-launcher.md` for the reusable workflow and verification matrix.

## Common Pitfalls

1. **A tool can be installed but still unavailable in the current shell.**
   The fix is usually PATH or shell startup state, not reinstalling.

2. User-local Python installs often need explicit PATH exposure.
   If `pip --user` or `uv tool install` is used, verify which user bin directory was created and make sure the shell sources it.
  
   - When using `uv pip` or `uv tool install`, ensure `greenlet` is installed as it is required for SQLAlchemy async support. Example: `uv pip install greenlet`. Ensure the uv-managed bin directory is on PATH.

   - **Environment Pollution (macOS):** `python3 -m venv` followed by `pip install` may fail with `TypeError: dataclass() got an unexpected keyword argument 'slots'`. This typically occurs when a `pip` version from a newer Python runtime (e.g., 3.11) is incorrectly invoked by an older Python interpreter (e.g., 3.9) due to PATH pollution. Use `uv venv` and `uv pip install` to create truly isolated temporary environments and avoid this conflict.

3. **Don't confuse login-shell and interactive-shell config.**
   Some PATH edits belong in `~/.zprofile`, others in `~/.zshrc`. If the user launches shells in multiple ways, update both when appropriate.

4. **Verify after reload.**
   Always test `command -v` again in a fresh shell before declaring success.

5. **brew doctor PATH warning after npm/global installs.**
   If `brew doctor` reports `/usr/bin` before `/opt/homebrew/bin` in PATH, the npm global shims may shadow Homebrew tools (or vice versa). Fix by adding `export PATH="/opt/homebrew/bin:$PATH"` to `~/.zshrc` and sourcing it. Verify with `echo $PATH` and `brew doctor`.

## Verification Checklist

- [ ] The command exists in the shell (`command -v <tool>`)
- [ ] The tool reports a version/help output
- [ ] The user knows which shell file was updated, if any
- [ ] A fresh shell can run the tool without manual PATH exporting
- [ ] `brew doctor` reports no PATH warnings (optional but recommended on macOS)

## Support files

- See `references/macos-cli-install.md` for a compact macOS install and PATH checklist.
- See `references/homebrew-cask-recovery.md` for non-interactive Homebrew cask recovery when a staged upgrade aborts on a sudo cleanup wall.
