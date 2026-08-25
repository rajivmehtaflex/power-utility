# macOS CLI install and PATH checklist

Use this when a command was installed but the user's interactive shell cannot find it.

## Quick checks

1. Confirm the executable exists:
   - `command -v <tool>`
   - `<tool> --version` or `<tool> --help`
2. Determine the install method:
   - Homebrew: usually already on PATH after shellenv
   - `pipx`: typically `~/.local/bin`
   - `pip install --user`: typically the user Python script directory
   - `uv tool install`: typically `~/.local/bin`
3. Refresh shell state:
   - `source ~/.zshrc`
   - `source ~/.zprofile`
   - `exec zsh`
4. Re-check in a fresh shell:
   - `zsh -ic 'command -v <tool> && <tool> --version'`

## PATH hygiene

- Add only the directory that actually contains the generated executable.
- Keep interactive-shell PATH edits in `~/.zshrc`.
- Keep login-shell PATH edits in `~/.zprofile`.
- Avoid duplicating the same PATH entry many times.

## When user-local Python tools are involved

If a `pip --user` install succeeds but the command is still missing, inspect the user Python bin directory and add it to PATH in both the current shell and the appropriate startup file.

Example directories:
- `~/.local/bin`
- `~/Library/Python/<version>/bin`

## Verification wording

Prefer saying:
- "Installed and verified in a fresh shell"

Avoid saying:
- "Installed" before confirming the command works in a new shell.
