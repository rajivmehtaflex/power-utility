# Media generation: image, tts, music, video

All four commands write the artifact to disk and print the **absolute file path
to stdout** — designed for pipelines. Capture stdout and you have the asset.

| Command | Default model | Default output |
|---|---|---|
| `image` | gemini-nano-banana-2.1 | `./gemini-image-<ts>-<rand>.<ext>` |
| `tts` | gemini-3.8-flash-tts | `./gemini-tts-<unix-ms>-<rand>.wav` |
| `music` | lyria-3.5 | `./gemini-music-<ts>-<rand>.<ext>` |
| `video` | gemini-omni-1.1-flash | `./gemini-video-<ts>.mp4` |

## image — generate and edit

```bash
gemini-api image "a lighthouse at sunset" --out assets/hero.png
gemini-api image "product shot, white bg" --aspect-ratio 16:9 --image-size 2K
# Conversational edit: capture turn 1's interaction ID, edit in turn 2
gemini-api image "make the sky stormy" --out shot.png --output-format json --jq .response_id
gemini-api image "add rain" --previous-interaction-id v1_...
```

Useful: `--aspect-ratio` (1:1, 16:9, 9:16…) · `--image-size` (512, 1K, 2K, 4K)
· `--output-mime-type image/jpeg` · `-i photo.png` to include a reference image
· `--raw-response` for the raw API payload instead of a file.

## tts — speech and voiceovers

```bash
gemini-api tts "Welcome to the show"                       # single speaker
gemini-api tts -f script.txt --voice Puck --out intro.wav  # from file
echo "hello" | gemini-api tts --stdin
gemini-api tts "Alice: hi. Bob: hello." --multi-speaker "Alice=Kore,Bob=Puck"
```

Voices: Kore, Puck, Zephyr, Charon, Fenrir, Aoede (default Kore). Output is
always 24 kHz mono **WAV** — `--out foo.mp3` still writes `foo.wav`. Multi-speaker
scripts need speaker labels at the start of each turn ("Alice: …").

## music

```bash
gemini-api music "upbeat synthwave with a driving bassline" --out bgm.wav
```

Prompt describes genre, mood, instrumentation, tempo.

## video — generate, then edit conversationally

```bash
gemini-api video "a timelapse of a city at night" --out clips/city.mp4
gemini-api video "ocean waves at dawn" --resolution 1080p --aspect-ratio 9:16
# Long renders: return immediately, resume later
ID=$(gemini-api video "20s aerial shot" --async --output-format json --jq '.id')
gemini-api video --resume "$ID"
```

`video` polls `agent status` internally until the render finishes (tune with
`--poll-interval`, `--poll-timeout`). `--async` skips the wait and returns an
operation ID you resume with `--resume`. Edits chain via
`--previous-interaction-id` like image.

## Shared rules

- `--out` extension is advisory: the API's returned MIME type decides the actual
  extension — ask for `hero.png` and the model returns JPEG, you get `hero.jpg`.
  Always use the path the CLI printed to stdout (or glob the directory); never
  assume the filename you passed to `--out` is what landed on disk.
- Dry-run first: `gemini-api image "..." --dry-run` prints the resolved request
  (no network, no cost) — cheap insurance before a long video render.
- `--raw-response` + `--jq` when you need IDs (for edits) instead of files.
- `-i` inputs count against the ~14 MB inline media limit; upload bigger files
  first (see [files-models-auth.md](files-models-auth.md)).

Full flags per command: `gemini-api image|tts|music|video --help` ·
docs: https://ai.google.dev/gemini-api/docs/image-generation,
/speech-generation, /music-generation, /video
