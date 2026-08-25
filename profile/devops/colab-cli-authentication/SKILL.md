---
name: colab-cli-authentication
description: Use for Colab CLI OAuth2/ADC authentication lifecycle.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: colab-operator, colab-ssh-setup
  hermes_tags: colab, oauth2, adc, authentication, pkce
  version: 1.0.0
---

# Google Colab CLI Authentication

## When to Use

Use this skill when a user needs to authenticate, reauthenticate, verify identity, log out of, or recover an OAuth authorization flow for the Google Colab CLI. Load `colab-operator` as well for runtime/session operations.

Manage the local authentication lifecycle for the `colab` CLI, including OAuth2 re-login, PKCE authorization-code handling, identity verification, and logout. This skill covers CLI authentication only; `colab auth` is a separate VM-side credential flow and must not be used to fix CLI authentication errors.

## First determine the authentication mode

Inspect the installed CLI before assuming a command exists:

```bash
PYTHONPATH="" colab help
PYTHONPATH="" colab version
```

The global `--auth={oauth2,adc}` option selects the CLI provider and must appear before the subcommand. In installed versions where the default is OAuth2, the token is normally cached at:

```text
~/.config/colab-cli/token.json
```

ADC is separate and is normally stored at:

```text
~/.config/gcloud/application_default_credentials.json
```

Never delete or revoke ADC merely because the user asked to log out of the Colab CLI's OAuth2 account.

## Verify the current identity

Use the CLI's read-only identity probe when available:

```bash
PYTHONPATH="" colab whoami
```

It reports the provider, email, scopes, audience, and token expiry without exposing the token contents. `colab sessions` is also a useful authenticated read-only check.

## OAuth2 re-login: preserve the PKCE session

When the cached OAuth2 token is absent or expired, the CLI prints a Google authorization URL and waits for a code. The authorization code is one-time and bound to the PKCE verifier held by the exact still-running CLI process that generated that URL.

1. Start one interactive PTY process:
   ```bash
   PYTHONPATH="" colab sessions
   ```
2. Open the exact URL printed by that process in a user-visible browser/preview pane.
3. Complete Google sign-in and consent.
4. Submit the returned code to the same still-running process.
5. Let that command finish, then verify with `PYTHONPATH="" colab whoami` or `PYTHONPATH="" colab sessions`.

Do not rerun `colab sessions` after opening the URL, do not abort the waiting process, and do not use a code copied from an older authorization attempt. A new process creates a new verifier and requires a new URL/code pair.

If the CLI reports `InvalidGrantError: (invalid_grant) Invalid code verifier`, discard the old code, start exactly one fresh PTY process, open its newly generated URL, and submit only the new code to that process.

On macOS Hermes terminal sessions, prefix commands with `PYTHONPATH=""` because an inherited Python path can interfere with the uv-installed Colab CLI.

## OAuth2 logout

There is no built-in `colab logout` command in the CLI versions covered here. To remove the locally cached Colab CLI OAuth2 login without touching ADC:

```bash
rm -f "$HOME/.config/colab-cli/token.json"
```

Verify logout by running `PYTHONPATH="" colab whoami`; it should start a fresh authorization flow rather than report the prior identity. This removes the local cached token but does not revoke the application's access from the Google account. If account-level revocation is explicitly requested, use Google's account security controls or the appropriate provider-specific revoke operation instead of silently revoking unrelated ADC credentials.

## Safety and reporting

- Never print token-file contents, authorization codes, client secrets, or refresh tokens in a final response.
- Report which credential store was changed: Colab CLI OAuth2 token, ADC, or neither.
- A successful `colab sessions` result after re-login is required before claiming that authentication was restored.
- If authorization is waiting on a human Google sign-in/code step, report that state plainly rather than claiming completion.

## Reference

See `references/oauth-pkce-recovery.md` for the reusable failure signature and exact recovery sequence.