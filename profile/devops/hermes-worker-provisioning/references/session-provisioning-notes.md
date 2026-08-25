# Session provisioning notes

Observed while provisioning Hermes worker profiles for the Silver Oak University student-activity-tracking workflow.

## What happened

- `hermes profile list` initially showed only `default`.
- Running the readiness checker with `--provision --json` created both requested worker profiles.
- After creation, `hermes profile list` showed the new profiles as stopped entries with aliases matching the profile names.
- `hermes profile show <name>` confirmed the profiles existed.

## Activation and config-path behavior

- `hermes profile use <name>` switches the active profile for the current shell session.
- After switching, `hermes config path` resolves to the profile-specific `~/.hermes/profiles/<name>/config.yaml`.
- On this installation, the profile-specific config file was not visible immediately after creation, but became visible once the profile was activated.

## Verification pitfall

- A readiness checker may report tool readiness from a weak proxy signal instead of a direct toolset inspection.
- Prefer verifying the active profile with:
  - `hermes config show`
  - `hermes tools list --platform cli`
  - `hermes config path`
  - `hermes profile show <name>`

## Practical takeaway

When provisioning a new worker profile, do not assume the config file is fully materialized the instant creation succeeds. Activate the profile and re-check the path before treating the profile as fully verified.