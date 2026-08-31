---
name: 1-minute-video-gen
description: Generate duration-aware videos through OpenRouter's asynchronous video API using five approved short-clip models. Use when a coding agent needs to create a longer video with prompt review, resolution/audio controls, and frame-continuous segment assembly.
license: MIT
compatibility: Requires Python 3.10+, the requests package, FFmpeg and FFprobe on PATH, network access, and OPENROUTER_API_KEY. Works with Agent Skills-compatible coding agents.
metadata:
  author: rajivmehtaflex
  version: "1.0.0"
  category: media
---

# 1 Minute Video Gen

Generate a user-approved long-form video by chaining supported OpenRouter video clips. The workflow preserves continuity by extracting the last frame of each completed clip and sending it as the next clip's `first_frame`.

The helper requires Python 3.10+, the `requests` package, and `ffmpeg`/`ffprobe` on `PATH`.

## Model boundary

Use only these model IDs. Reject any other model instead of silently substituting one:

- `bytedance/seedance-2.0-mini`
- `bytedance/seedance-1-5-pro`
- `alibaba/wan-2.6`
- `bytedance/seedance-2.0-fast`
- `alibaba/wan-3.0`

Before generating, query `GET https://openrouter.ai/api/v1/videos/models` and validate the chosen model's `supported_durations`. Never send a duration that the model does not advertise. If 60 seconds is unsupported, create a sequence of supported-duration clips and concatenate them locally; trim the final file to the requested duration.

## Required conversation gate

Ask the user for these inputs before execution:

1. `model-name` — show the five allowed model IDs.
2. `duration` — positive number of seconds; default to 60 only if the user accepts that default.
3. `resolution` — ask after reading the selected model's `supported_resolutions`; never assume 720p.
4. `audio` — explicitly ask whether generated audio is required (`yes`/`no`) and validate it against the model's `generate_audio` capability.
5. `Prompt` — the intended video content.

Rewrite the prompt into a concise, duration-aware segment plan. Preserve the user's subject, action, style, and aspect ratio. For multiple clips, keep character descriptions, setting, lighting, camera language, and visual style consistent; label each segment's role and duration. Show the complete rewritten prompt/segment plan verbatim to the user.

Show the selected resolution and audio setting in the preview. Explain that OpenRouter's advertised `from` price is the lowest available pricing tier and that resolution, audio mode, duration, and the number of generated segments affect the actual cost.

Do not submit an API request until the user explicitly confirms the displayed plan. A confirmation such as `yes`, `proceed`, or `run it` is required after the preview.

## API and continuity workflow

- Obtain the key from the shell environment's `OPENROUTER_API_KEY` value. Never print, persist, or expose the key.
- Use `POST /api/v1/videos`; the response is asynchronous and returns a job ID plus `polling_url`.
- Send the user's validated `resolution` and `generate_audio` choices in every segment request.
- Poll until `completed` or `failed`, then download the completed content.
- For segment 2 onward, extract the previous MP4's last frame with FFmpeg and send it as a local Base64 `data:image/jpeg;base64,...` URL in:

  ```json
  {
    "frame_images": [
      {
        "type": "image_url",
        "image_url": {"url": "data:image/jpeg;base64,..."},
        "frame_type": "first_frame"
      }
    ]
  }
  ```

- Use `frame_images` for exact continuation. Use `input_references` only when the user wants loose style/content guidance.
- Before concatenating, remove the first decoded frame from every continuation clip so the conditioning frame is not duplicated at clip boundaries. Then concatenate clips with FFmpeg and trim to the requested duration. Keep intermediate clips and frames in a temporary directory unless the user requests otherwise.
- Use the reusable implementation in [scripts/generate_video.py](scripts/generate_video.py). It always prompts interactively for model, duration, resolution, audio, and prompt, accepts an optional output path, and has its own final confirmation gate as a safety net.

## Failure handling

- Stop before generation if the key is missing, the model is outside the allowlist, FFmpeg/FFprobe is unavailable, or the selected model reports no usable durations.
- If a job fails, report the API error and do not continue to later segments.
- If a model does not support `frame_images`, report that continuity chaining is unavailable for that model rather than pretending the frame was used.
