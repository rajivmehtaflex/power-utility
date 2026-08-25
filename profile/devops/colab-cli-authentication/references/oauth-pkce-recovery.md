# OAuth2/PKCE Recovery Reference

## Failure signature

When a code from an earlier or aborted authorization prompt is submitted to a different CLI process, the Colab CLI can fail with:

```text
InvalidGrantError: (invalid_grant) Invalid code verifier.
```

This indicates a PKCE process/code mismatch, not necessarily a bad Google account or missing scope.

## Recovery recipe

1. Start exactly one interactive process:
   ```bash
   PYTHONPATH="" colab sessions
   ```
2. Capture the URL printed by that process.
3. Open that exact URL in the user-visible preview pane.
4. Complete Google sign-in and consent.
5. Submit the newly displayed authorization code to the same live process.
6. Wait for the command to finish and verify:
   ```bash
   PYTHONPATH="" colab whoami
   ```

If the process was aborted, the URL was replaced, or the code came from another attempt, discard the code and restart from step 1. Never combine a code from one prompt with a verifier from another.

## Logout scope

For OAuth2 logout, remove only:

```text
~/.config/colab-cli/token.json
```

Do not modify `~/.config/gcloud/application_default_credentials.json` unless the user explicitly requests ADC revocation. The two credential stores serve different authentication modes.
