# explainify

Turn a topic, URL, pasted text, or markdown file into an accurate, audience-appropriate
explanation: STE-inspired simplified English (`.md`) or a short silent explainer video
(MP4, dark mathematical animation) rendered locally. The writing is an approximate
profile inspired by ASD-STE100 — not validated for conformity. The video is silent.

## Formats

| Format key | Output | v0.1 status |
|---|---|---|
| `asd-ste100` | `<slug>-asd-ste100.md` | Available; STE-inspired and explicitly approximate |
| `explainer-video` | Silent MP4 plus a reproducibility bundle (render script, storyboard, verification notes) | Available; dark mathematical animation, no affiliation claim |
| `diagram`, `html-page` | None | Reserved; unavailable in v0.1 — supported formats are offered instead |

## Usage

Invoke with "explainify" or phrases such as "explain X in simplified English" or "make
an explainer video of X". Inputs: a topic, a URL, pasted text, or a UTF-8 `.md`/`.txt` file.

Defaults: writing format; audience is a curious reader unfamiliar with the concept;
output goes to a fresh run directory `./explainify-output/<slug>-YYYYMMDD-HHMMSS/`
relative to the user's working directory, never the installed skill directory.

Deliverables — writing: one file, `<slug>-asd-ste100.md` (profile label, explanation,
source attribution, scope limitations). Video: `<slug>-explainer.mp4`,
`<slug>-render.py`, `<slug>-storyboard.json` (teaching brief and provenance), and
`<slug>-verification.md` (checks, limitations, versions). Reproduce a video bundle
from its directory with
`uv run <slug>-render.py --storyboard <slug>-storyboard.json --output <new>.mp4`.

Full workflow, verification gates, and failure reporting: [SKILL.md](SKILL.md).

## Requirements

| Capability | Needed for |
|---|---|
| File access | All formats; writing needs file access only |
| Web retrieval | URL inputs |
| Command execution; uv (Python 3.11+); ffmpeg and ffprobe with an available H.264 encoder | Video |
| Image inspection | Full video verification |

Without image inspection, a video can still be produced and delivered, but it ships
marked **visually unverified** and does not pass the full video acceptance gate.

Preflight is read-only and never installs anything: `scripts/check_env.py --format explainer-video`
or `scripts/check_env.py --format asd-ste100` — exit 0 means the local runtime preflight
passes, exit 1 means prerequisites are missing.

## Installation

Public install:

```text
npx skills add rajivmehtaflex/power-utility --skill explainify
```

Add `--global --copy` for a copied user-scope installation instead of a project-scoped
one. Check for an existing skill at the destination before copying or replacing it; no
collision-free naming is claimed.

Documented discovery locations:

| Client | Documented location |
|---|---|
| Cursor | `~/.agents/skills/explainify/` or project `.agents/skills/explainify/` |
| Claude Code | `~/.claude/skills/explainify/` or project `.claude/skills/explainify/` |
| Other clients | No universal location; consult that client's current documentation |

Documented is not tested:

- The table lists locations those clients document themselves; it is not a claim that
  any installation has been tested in any client.
- Local installer verification results are recorded in
  `docs/superpowers/verification/explainify/results.md` in the source repository —
  development evidence, not part of the installed package.
- The public install command works only after the package has been pushed to the
  public repository ref.

## Package contents

```text
├── SKILL.md                      # Shared workflow, dispatch, verification, delivery
├── scripts/check_env.py          # Read-only, format-specific preflight
├── scripts/render_video.py       # Template copied and adapted per topic
├── references/asd-ste100.md      # Approximate STE-inspired writing profile
├── references/video-style.md     # Visual teaching, pacing, inspection guidance
├── assets/storyboard.schema.json # Teaching/timing contract, not a drawing DSL
├── tests/                        # Runtime contract tests
├── README.md
└── LICENSE
```

The package is self-contained, with no dependencies on the surrounding repository. Runs
never modify installed templates, references, or scripts; outputs go to the run directory.

## License

MIT — see [LICENSE](LICENSE). It covers the original skill code and writing.
