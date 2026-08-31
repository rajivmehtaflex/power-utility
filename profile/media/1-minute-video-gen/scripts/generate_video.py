#!/usr/bin/env python3
"""Generate a duration-controlled OpenRouter video by chaining short clips.

The script is intentionally interactive. It never starts a paid generation
job without showing the final segment plan and receiving an explicit ``yes``
confirmation.
"""

from __future__ import annotations

import argparse
import base64
import pathlib
import shutil
import subprocess
import tempfile
import time
from typing import Any

import requests


BASE_URL = "https://openrouter.ai/api/v1"
POLL_INTERVAL_SECONDS = 30
POLL_TIMEOUT_SECONDS = 45 * 60

ALLOWED_MODELS = {
    "bytedance/seedance-2.0-mini",
    "bytedance/seedance-1-5-pro",
    "alibaba/wan-2.6",
    "bytedance/seedance-2.0-fast",
    "alibaba/wan-3.0",
}


def read_key_from_env_command() -> str:
    """Read OPENROUTER_API_KEY through the shell's env command without printing it."""
    completed = subprocess.run(
        ["env"],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in completed.stdout.splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY was not found in the shell environment.")


def ask(value: str | None, label: str) -> str:
    result = value.strip() if value else ""
    while not result:
        result = input(f"{label}: ").strip()
    return result


def parse_duration(value: str | None) -> int:
    raw = ask(value, "Duration in seconds")
    try:
        duration = int(raw)
    except ValueError as exc:
        raise ValueError("Duration must be a positive whole number of seconds.") from exc
    if duration <= 0:
        raise ValueError("Duration must be greater than zero.")
    return duration


def choose_model(value: str | None) -> str:
    allowed = sorted(ALLOWED_MODELS)
    raw = value.strip() if value else ""
    while raw not in ALLOWED_MODELS:
        if raw:
            print("That model is not allowed. Choose one of:")
        print("\n".join(f"  - {model}" for model in allowed))
        raw = input("Model name: ").strip()
    return raw


def choose_resolution(value: str | None, model_info: dict[str, Any]) -> str:
    supported = [str(item) for item in model_info.get("supported_resolutions", [])]
    if not supported:
        raise RuntimeError("The selected model did not report supported resolutions.")

    raw = value.strip() if value else ""
    while raw not in supported:
        if raw:
            print("That resolution is not supported. Choose one of:")
        print("  - " + "\n  - ".join(supported))
        raw = input("Resolution: ").strip()
    return raw


def choose_audio(model_info: dict[str, Any]) -> bool:
    raw = ""
    while raw not in {"yes", "no"}:
        raw = input("Generate audio? (yes/no): ").strip().lower()
    if raw == "yes" and model_info.get("generate_audio") is False:
        raise ValueError("The selected model does not support generated audio.")
    return raw == "yes"


def get_model_info(session: requests.Session, model: str) -> dict[str, Any]:
    response = session.get(f"{BASE_URL}/videos/models", timeout=60)
    response.raise_for_status()
    models = response.json().get("data", [])
    info = next((item for item in models if item.get("id") == model), None)
    if not info:
        raise RuntimeError(f"Model {model!r} was not returned by the video models API.")
    durations = info.get("supported_durations")
    if not isinstance(durations, list) or not durations:
        raise RuntimeError(f"Model {model!r} did not report supported durations.")
    return info


def plan_durations(target_seconds: int, supported: list[int]) -> list[int]:
    durations = sorted({int(value) for value in supported if int(value) > 0})
    if not durations:
        raise ValueError("The selected model has no usable supported durations.")

    plan: list[int] = []
    remaining = target_seconds
    while remaining > 0:
        choices = [duration for duration in durations if duration <= remaining]
        chosen = max(choices) if choices else max(durations)
        plan.append(chosen)
        remaining -= chosen
    return plan


def build_segment_prompts(prompt: str, plan: list[int]) -> list[str]:
    total = len(plan)
    return [
        (
            f"{prompt.strip()}\n\n"
            f"This is segment {index + 1} of {total}, lasting {seconds} seconds. "
            "Maintain the same characters, setting, lighting, color grade, "
            "camera language, and visual style across all segments. "
            "Continue naturally from the supplied first frame."
        )
        for index, seconds in enumerate(plan)
    ]


def image_data_url(image_path: pathlib.Path) -> str:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def extract_last_frame(video_path: pathlib.Path, image_path: pathlib.Path) -> None:
    frame_count = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_frames",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        text=True,
    ).strip()
    if frame_count.isdigit() and int(frame_count) > 0:
        video_filter = f"select=eq(n\\,{int(frame_count) - 1}),format=yuvj420p"
        seek_args: list[str] = []
    else:
        stream_duration = float(
            subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(video_path),
                ],
                text=True,
            ).strip()
        )
        seek_args = ["-ss", f"{max(0.0, stream_duration - 0.1):.3f}"]
        video_filter = "format=yuvj420p"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            *seek_args,
            "-i",
            str(video_path),
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-update",
            "1",
            "-vf",
            video_filter,
            "-q:v",
            "2",
            str(image_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def drop_first_frame(video_path: pathlib.Path, output_path: pathlib.Path) -> None:
    """Remove the conditioning frame before assembling a continuation clip."""
    frame_rate = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=avg_frame_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        text=True,
    ).strip()
    numerator, denominator = (int(value) for value in frame_rate.split("/", 1))
    frame_duration = denominator / numerator

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-vf",
            "select=gte(n\\,1),setpts=PTS-STARTPTS",
            "-af",
            f"atrim=start={frame_duration},asetpts=PTS-STARTPTS",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def submit_and_download(
    session: requests.Session,
    model: str,
    prompt: str,
    duration: int,
    resolution: str,
    generate_audio: bool,
    output_path: pathlib.Path,
    first_frame: pathlib.Path | None = None,
) -> None:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": "16:9",
        "generate_audio": generate_audio,
    }
    if first_frame:
        payload["frame_images"] = [
            {
                "type": "image_url",
                "image_url": {"url": image_data_url(first_frame)},
                "frame_type": "first_frame",
            }
        ]

    response = session.post(f"{BASE_URL}/videos", json=payload, timeout=60)
    response.raise_for_status()
    job = response.json()
    job_id = job.get("id")
    polling_url = job.get("polling_url")
    if not job_id or not polling_url:
        raise RuntimeError(f"OpenRouter returned an unexpected submit response: {job}")

    print(f"Submitted job {job_id} ({duration}s)")
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)
        poll_response = session.get(polling_url, timeout=60)
        poll_response.raise_for_status()
        status = poll_response.json()
        state = status.get("status")
        print(f"  Job {job_id}: {state}")

        if state == "failed":
            raise RuntimeError(status.get("error", f"Job {job_id} failed."))
        if state == "completed":
            urls = status.get("unsigned_urls") or []
            if urls:
                download_response = session.get(urls[0], timeout=300)
            else:
                content_url = f"{BASE_URL}/videos/{job_id}/content?index=0"
                download_response = session.get(content_url, timeout=300)
            download_response.raise_for_status()
            output_path.write_bytes(download_response.content)
            return

    raise TimeoutError(f"Job {job_id} did not complete within the polling timeout.")


def stitch_and_trim(
    segment_paths: list[pathlib.Path],
    duration: int,
    output_path: pathlib.Path,
) -> None:
    concat_path = output_path.parent / "concat.txt"

    def concat_line(path: pathlib.Path) -> str:
        escaped = str(path.resolve()).replace("'", "'\\''")
        return f"file '{escaped}'"

    concat_path.write_text(
        "\n".join(concat_line(path) for path in segment_paths) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-t",
            str(duration),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="one_minute_video.mp4")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = choose_model(None)
    duration = parse_duration(None)
    output_path = pathlib.Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    model_info = get_model_info(session, model)
    resolution = choose_resolution(None, model_info)
    generate_audio = choose_audio(model_info)
    prompt = ask(None, "Prompt")
    supported_durations = [int(value) for value in model_info["supported_durations"]]
    plan = plan_durations(duration, supported_durations)
    prompts = build_segment_prompts(prompt, plan)

    print("\nFinal generation plan")
    print(f"Model: {model}")
    print(f"Requested duration: {duration}s")
    print(f"Resolution: {resolution}")
    print(f"Audio: {'enabled' if generate_audio else 'disabled'}")
    print(f"Supported durations: {sorted(supported_durations)}")
    print(f"Segments: {len(plan)} ({sum(plan)}s before final trim)\n")
    for index, (seconds, segment_prompt) in enumerate(zip(plan, prompts), start=1):
        print(f"--- Segment {index}: {seconds}s ---")
        print(segment_prompt)

    confirmation = input("\nType 'yes' to start generation: ").strip().lower()
    if confirmation != "yes":
        print("Cancelled before any video-generation request was submitted.")
        return

    api_key = read_key_from_env_command()
    session.headers.update(
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    )

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not shutil.which("ffprobe"):
        raise RuntimeError("Both ffmpeg and ffprobe must be installed and on PATH.")

    with tempfile.TemporaryDirectory(prefix="openrouter-video-") as temp_dir:
        work_dir = pathlib.Path(temp_dir)
        segment_paths: list[pathlib.Path] = []
        previous_video: pathlib.Path | None = None

        for index, (seconds, segment_prompt) in enumerate(zip(plan, prompts), start=1):
            first_frame = None
            if previous_video:
                first_frame = work_dir / f"frame_{index}.jpg"
                extract_last_frame(previous_video, first_frame)

            segment_path = work_dir / f"segment_{index}.mp4"
            submit_and_download(
                session,
                model,
                segment_prompt,
                seconds,
                resolution,
                generate_audio,
                segment_path,
                first_frame,
            )
            assembly_path = segment_path
            if previous_video:
                assembly_path = work_dir / f"segment_{index}_without_duplicate_frame.mp4"
                drop_first_frame(segment_path, assembly_path)
            segment_paths.append(assembly_path)
            previous_video = segment_path

        stitch_and_trim(segment_paths, duration, output_path)

    print(f"Created {output_path}")


if __name__ == "__main__":
    main()
