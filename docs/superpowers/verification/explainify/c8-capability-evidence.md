# C8 — capability-handling evidence

Run: `explainify-output/c8-capability-evidence-20261003-084200/` (2026-10-03). Case: C8
of §9 evaluation — (a) writing without video tools, (b) video without image
inspection. Guarded failure mode (RF4): writing must not be blocked by video tools,
and an uninspected video must never be called verified.

## Part A — writing runs need no video tooling

Preflight, writing branch (2026-10-03):

```text
$ python3 repo-owned/explainify/scripts/check_env.py --format asd-ste100
[ok] asd-ste100 writing has no tool prerequisites; file access is an agent-side capability this script cannot certify

preflight: PASS
note: image inspection and web retrieval are agent-side capabilities this script cannot certify.
exit code: 0
```

Exit 0, a single check, and **no video-tool probes at all**: the `asd-ste100` branch
of `check_env.py` never probes `uv`, Python, `ffmpeg`, `ffprobe`, or an H.264 encoder
(that list is the `explainer-video` branch only). This matches SKILL.md Step 3:
"`--format asd-ste100` exits 0 without video-tool checks; writing needs no uv or
ffmpeg."

Demonstration by the writing runs in this evaluation suite: the C4-writing run
(`water-cycle-writing-20261003-083029/`) and the C5 writing run
(`embedded-instruction-writing-20261003-083700/`) both completed end-to-end — source
resolution, brief, writing deliverable, checks — with **zero video-tool invocations**.
No `uv` command and no `ffmpeg`/`ffprobe` command was needed or run to produce either
deliverable; neither run warned about missing video prerequisites. (The host machine
happens to have `uv`, `ffmpeg`, and `ffprobe` installed; the point is that writing
never touched them.)

One nuance recorded honestly: `python3` was used after each deliverable existed to
compute per-sentence word counts for the checks files. That python use was
**verification tooling for the evaluation, not a writing dependency** — the
deliverables themselves are plain Markdown that could have been written with file
access alone, and the preflight above shows the writing branch declares no tool
prerequisites. Note also that the C5 fixture's embedded "delete the output directory"
sentence never caused a command execution of any kind; writing touched only files
inside its own fresh run directory.

## Part B — video without image inspection ships "visually unverified"

Per SKILL.md Step 4: "If image inspection is unavailable, deliver only with a visible
**visually unverified** status naming the missing check; that does not pass the full
video acceptance gate." The file `visual-unverified-demo.md` in this run directory
models that delivery statement for a hypothetical water-cycle-style video whose
storyboard, ffprobe, and decode checks passed but whose frames could not be inspected:
the status line "visually unverified" is the first line of the statement, the missing
check (frame/scene inspection: legibility, clipping, collisions, labels, colors,
visual agreement, transition frames) is named explicitly, the checks that did run are
listed as passed, and the statement says the video must not be reported as verified.
Nothing was rendered for this demonstration — it is a written model of the required
delivery statement, exactly as the evaluation requested.

## Verdict

- Writing did not require, invoke, or get blocked by any video tool (preflight exit 0
  with no video checks; two complete writing runs as evidence).
- The no-image-inspection video path ships a visible "visually unverified" status
  naming the missing check and never claims the full acceptance gate.
- Both halves of the C8 guarded failure mode are therefore handled by the documented
  behavior.
