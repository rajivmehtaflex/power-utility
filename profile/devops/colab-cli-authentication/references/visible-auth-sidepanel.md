# Visible Colab OAuth side-panel auth

Use this when the user wants the Colab CLI OAuth2 login shown in Hermes rather than hidden in a terminal-only flow.

## Working flow

1. Remove the cached Colab CLI token:
   ```bash
   rm -f "$HOME/.config/colab-cli/token.json"
   ```
2. Start one fresh auth process and keep it running:
   ```bash
   PYTHONPATH="" colab whoami
   ```
3. Copy the exact authorization URL printed by that process into `open_preview` so the Google sign-in page appears in the Hermes side panel.
4. Use `read_preview` to confirm the page title/contents if needed; the chooser should show the available Google accounts.
5. Have the user pick the desired account in that side panel and finish consent.
6. Submit the returned authorization code to the same still-running terminal process.
7. Verify the identity switch with:
   ```bash
   PYTHONPATH="" colab whoami
   ```

## Pitfalls

- The code is bound to the still-running process that printed the URL; do not restart the auth command after opening the page.
- A new auth process creates a new PKCE verifier, so the previous code will no longer work.
- The preview pane is for visibility; the authorization code still goes back to the terminal process.
