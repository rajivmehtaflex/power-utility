---
name: github-codespace-ssh
description: Manage and SSH into GitHub Codespaces via gh CLI.
metadata:
  author: Hermes
  hermes_tags: GitHub, Codespaces, SSH, VSCode, gh-cli
  platforms: macos, linux, windows
  version: 0.1.0
---

# GitHub Codespace SSH Connectivity

Manage GitHub Codespaces and generate OpenSSH configurations to enable remote development via VS Code or standard SSH clients. This workflow relies on the `gh` CLI to handle authentication and proxying.

## When to Use
- "List my active codespaces"
- "Connect to a codespace via SSH"
- "Generate SSH config for a codespace"
- "Fix HTTP 403 error when listing codespaces"

## Prerequisites
- `gh` CLI installed and authenticated.
- VS Code with the **Remote - SSH** extension (for GUI connection).

## How to Run
Invoke GitHub CLI commands through the `terminal` tool.

## Quick Reference
- List: `gh codespace list`
- Switch User: `gh auth switch --user <username>`
- Fix Scope: `gh auth refresh --hostname github.com --scopes codespace`
- Get Config: `gh codespace ssh --codespace <name> --config`

## Procedure

1. **Identify Active Account**
   Check which account is currently active:
   ```bash
   gh auth status
   ```

2. **Switch Account (If Necessary)**
   If the codespace belongs to a different authenticated account:
   ```bash
   gh auth switch --user <username>
   ```

3. **List Available Codespaces**
   Retrieve the list of codespaces for the active user:
   ```bash
   gh codespace list
   ```

4. **Handle Missing Scopes (HTTP 403)**
   If `gh codespace list` returns a 403 Forbidden error regarding the "codespace" scope:
   - Run the refresh command:
     ```bash
     gh auth refresh --hostname github.com --scopes codespace
     ```
   - Follow the prompt to visit `https://github.com/login/device` and enter the provided one-time code.

5. **Generate SSH Configuration**
   Generate the OpenSSH config block for a specific codespace:
   ```bash
   gh codespace ssh --codespace <codespace-name> --config
   ```

6. **Configure Local SSH**
   Add the output from the previous step to your local SSH configuration file (`~/.ssh/config`).

7. **Connect via VS Code**
   - Press `Cmd + Shift + P` $\rightarrow$ **Remote-SSH: Connect to Host...**
   - Select the hostname (e.g., `cs.<name>.main`) generated in the config.

## Pitfalls
- **Scope Mismatch:** Running `gh auth refresh` while the wrong account is active will grant the scope to that account, not the target one. Always `gh auth switch` first.
- **Device Auth Timeouts:** `gh auth refresh` prompts can time out in non-interactive terminals. Use a generous `timeout` in the `terminal` tool.
- **SSH Server Missing:** The codespace must have an SSH server installed. If it fails to connect, ensure the `devcontainer.json` includes the `sshd` feature.

## Verification
Run `gh codespace list`. If it returns a list of codespaces without a 403 error, the scope is correctly configured.
