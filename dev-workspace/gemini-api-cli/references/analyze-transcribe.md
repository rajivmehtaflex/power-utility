# Understanding files: analyze & transcribe

Both commands take `-i/--input` (repeatable): a local path, a `files/<id>` from
the Files API, or a YouTube URL. Local files are sent inline; requests stay
under 20 MB base64-included (~14 MB of media) — upload larger files first with
`gemini-api files upload` and pass the returned `files/<id>`.

## analyze — ask questions about anything

```bash
gemini-api analyze -i report.pdf "Summarize the key findings"
gemini-api analyze -i photo.jpg                          # default question: describe in detail
gemini-api analyze -i files/abc123 "List every speaker with timestamps"
gemini-api analyze -i https://youtu.be/dQw4w9WgXcQ "What happens at 1:00?"
gemini-api analyze -i a.png -i b.png "What changed between these?"
```

Default model gemini-3.8-flash; `--system` steers the analysis; `--stdin` adds
text after the media, before the question. stdout is the model's answer only —
pipe-friendly. The request is not stored server-side.

## transcribe — audio/video → text

```bash
gemini-api transcribe -i interview.mp3                       # markdown, speakers, timestamps
gemini-api transcribe -i call.wav --format srt --out call.srt
gemini-api transcribe -i files/abc123 --format json --no-speakers
gemini-api transcribe -i a.mp3 -i b.mp3 --out ./transcripts/  # dir when multiple inputs
```

Formats: `md` (default), `text`, `json`, `srt` (alias `captions`). Flags:
`--no-speakers`, `--no-timestamps` (ignored for srt), `--out`. stdout prints one
absolute artifact path per line — capture it. An existing artifact is replaced.

## Choosing between them

- Want an **answer about** content ("what changed?", "list the speakers",
  "summarize chapter 3") → `analyze`.
- Want the **content itself** as text (captions, a transcript file) → `transcribe`.
- Both on the same recording is normal: transcribe for the artifact, analyze
  for insight about it.

## Gotchas

- `transcribe --format srt` can return a single long cue spanning the whole
  clip — valid SRT, but poor captioning. When you need broadcast-style captions,
  re-segment with a text model: `gemini-api generate -i <audio> --stream=false
  "<captioning prompt — 1–5 s cues, max 2 lines, ~42 chars/line, verbatim,
  output raw SRT only>"`, save the output as `.srt`, and verify structure
  (numbered cues + `HH:MM:SS,mmm --> HH:MM:SS,mmm`, timestamps within audio
  duration).
- Multiple `-i` flags = one analysis across all inputs (e.g. comparisons);
  `transcribe` processes them sequentially instead.
- `--mime-type` works with exactly one input, for when detection guesses wrong.
- Exit code `3` = fix auth, not the command.

Full flags: `gemini-api analyze --help` / `gemini-api transcribe --help` ·
docs: https://ai.google.dev/gemini-api/docs/audio
