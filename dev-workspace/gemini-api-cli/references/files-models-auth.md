# Files, models, and auth

## files — upload, list, inspect, delete (48-hour retention)

The inline request limit is 20 MB base64-included (~14 MB of media). Anything
bigger goes through the Files API first:

```bash
gemini-api files upload big-lecture.mp4           # → files/<id>
gemini-api analyze -i files/<id> "Summarize each section"
gemini-api files list --output-format json        # see what's still alive
gemini-api files get <id>                         # metadata + processing state
gemini-api files delete <id>
gemini-api files register gs://bucket/data.csv    # register GCS object, no copy
gemini-api files generated-files-list             # files made on your behalf
```

Uploaded files live **48 hours** — re-upload rather than caching IDs across days.

## models — pick the right model

```bash
gemini-api models            # offline curated catalog, grouped by capability
gemini-api models list       # live API model list
gemini-api models get <id>   # version, token limits, supported methods
```

Bare `models` makes no network call — use it freely to check names before
passing `-m/--model` anywhere. Common families: gemini-3.8-flash (text/analyze),
gemini-nano-banana-2.1 (image), gemini-3.8-flash-tts (speech), lyria-3.5
(music), gemini-omni-1.1-flash (video), deep-research-* and antigravity-*
(managed agents).

## auth & configure

```bash
gemini-api whoami                          # what auth/params are in effect
gemini-api configure                       # interactive setup (TUI)
gemini-api configure --api-key "$KEY"      # store key in OS keychain
gemini-api configure --default-output-format json
gemini-api auth --help                     # login/logout, credential mgmt
```

Resolution priority: **CLI flags > environment (`GEMINI_API_KEY`) > OS keychain
> `~/.config/gemini-api/config.yaml`**. Secrets live in the OS keyring, not the
config file, when one is available (`--no-keyring` forces config-file storage —
avoid it unless keychain access is blocked).

For CI/agents, the cleanest setup is a `GEMINI_API_KEY` env var; nothing else
to configure. Exit code `3` from any command means auth failed.

## Useful global flags (every command)

`--api-key` · `--timeout 30s` · `--server-url` (point at a mock/proxy) ·
`-H/--header` custom headers · `--dry-run` (no network, no keychain read) ·
`--usage` (machine-readable CLI schema, KDL) · `--no-interactive`.
Full list: `gemini-api --help-global`.
