---
name: gemini-api-cli
description: Drive the Google Gemini API from the shell with the stateless gemini-api CLI. Generate text (second opinions, code review, explanations), create and edit images, generate voiceovers (TTS, multi-speaker), music, and video, analyze PDFs, images, audio, video, CSVs, and YouTube URLs, transcribe recordings to SRT/JSON/markdown, and delegate long multi-step work to background managed agents (Deep Research, Antigravity) with interaction-ID capture and polling. Use this whenever a task needs media generation, multimodal file understanding, captions or transcripts, a Gemini model's opinion, or a background research/coding run — even when the user does not name Gemini. The CLI is self-describing (--help, --usage, --schema); validate any call offline with --dry-run; script results out with --output-format json and --jq.
license: Apache-2.0
compatibility: Requires the gemini-api CLI binary on PATH (v0.4+), network access to the Gemini API, and a GEMINI_API_KEY (env var, OS keychain, or `gemini-api configure`). Check any time with scripts/check_setup.sh.
metadata:
  author: rajivmehtaflex
  version: 1.1.0
  upstream: https://github.com/google-gemini/gemini-api-cli
---

# gemini-api-cli

Call Google's Gemini models and managed agents from the shell: text, images,
voice, music, video, document/audio/video analysis, transcription, and
background agents — through one stateless, self-describing binary.

This skill is a router, not an encyclopedia. The CLI documents itself better
than any bundled copy could (`gemini-api <cmd> --help`, `--usage`, `--schema`),
and its flags evolve fast — the references below distill workflows and gotchas,
then hand off to the CLI's own help for the full live flag set.

## Preflight — run once per session

```bash
bash scripts/check_setup.sh
```

If the binary is missing, offer to install it (macOS/Linux):

```bash
curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-api/main/scripts/install.sh | bash
```

Auth priority is: CLI flags > env vars (`GEMINI_API_KEY`) > OS keychain >
`~/.config/gemini-api/config.yaml`. Never store a key inside a repo or skill.

## Routing — pick the command, then read only the reference you need

| Task | Command | Reference |
|---|---|---|
| Text answer, second opinion, code review | `gemini-api generate` | [references/generate-text.md](references/generate-text.md) |
| Create/edit an image | `gemini-api image` | [references/media-generation.md](references/media-generation.md) |
| Voiceover / speech | `gemini-api tts` | [references/media-generation.md](references/media-generation.md) |
| Music | `gemini-api music` | [references/media-generation.md](references/media-generation.md) |
| Video | `gemini-api video` | [references/media-generation.md](references/media-generation.md) |
| Ask questions about a file or YouTube URL | `gemini-api analyze` | [references/analyze-transcribe.md](references/analyze-transcribe.md) |
| Captions / transcript | `gemini-api transcribe` | [references/analyze-transcribe.md](references/analyze-transcribe.md) |
| Long multi-step task, run in background | `gemini-api agent run --background` | [references/managed-agents.md](references/managed-agents.md) |
| Upload big files (>~14 MB), list models, auth setup | `files` / `models` / `configure` | [references/files-models-auth.md](references/files-models-auth.md) |
| Exact request control (raw JSON body) | `gemini-api agent run --body @req.json` | [references/managed-agents.md](references/managed-agents.md) |

Default models per command (as of v0.4.4): `generate`/`analyze`/`transcribe` →
gemini-3.8-flash · `image` → gemini-nano-banana-2.1 · `tts` → gemini-3.8-flash-tts ·
`music` → lyria-3.5 · `video` → gemini-omni-1.1-flash. List everything with
`gemini-api models` (offline catalog) or `gemini-api models list` (live).

## Ground rules — how to drive the CLI like a machine

1. **Capture output structurally.** Use `--output-format json` plus `--jq` when
   you need a field (an ID, a path); media commands already print the written
   file path to stdout — capture that and keep building with it.
2. **Dry-run anything unfamiliar.** `--dry-run` validates the request, prints
   the resolved curl (credentials redacted), touches no network and no keychain.
   Use it before the first live call of a new shape, and as a self-check that
   your flags parsed the way you intended.
3. **Don't guess flags — ask the CLI.** `<cmd> --help` for humans, `--usage`
   for the machine-readable KDL schema, `--schema` for the exact JSON request
   body shape. Inventing flags fails with exit code 2.
4. **Read exit codes.** `0` ok · `1` runtime (retry may help) · `2` usage (your
   command is wrong — fix it, don't retry) · `3` auth (fix credentials, don't
   retry). Exit 3 means point the user at `gemini-api configure` or
   `GEMINI_API_KEY`.
5. **Stay non-interactive.** Add `--no-interactive` in scripts and CI so the
   CLI never blocks on a TTY prompt.
6. **Files >20 MB (base64 included, ~14 MB media)** must go through
   `gemini-api files upload` first; pass the returned `files/<id>` to
   `-i/--input`. Uploaded files expire after 48 hours.

## Escalation path

Intent commands (`generate`, `image`, `analyze`, …) cover common shapes. When
they can't express what you need, escalate to the generic interaction command
with an exact JSON body — see [references/managed-agents.md](references/managed-agents.md).

Docs: https://ai.google.dev/gemini-api/docs · CLI source:
https://github.com/google-gemini/gemini-api-cli
