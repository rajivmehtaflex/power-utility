# gemini-api-cli

Cross-agent [Agent Skill](https://agentskills.io/specification) for the Google
`gemini-api` CLI. Install it once and your coding agent can generate media,
read any file, transcribe recordings, and run long research jobs in the
background — most of which the agent cannot do on its own.

You never type `gemini-api` commands yourself. You describe the outcome; the
skill supplies the command, flags, and output handling.

## Example prompts

Paste any of these into Claude Code, Codex, Cursor, Antigravity, or any agent
that has this skill installed. Naming Gemini is optional — the skill routes on
the task, not the vendor.

**Images**

> Make a hero banner for the launch page — abstract isometric city, 16:9 — and
> drop it in `static/img/`.

> Edit `assets/product.png`: remove the background and put it on a soft
> gradient.

**Voice, music, video**

> Read `scripts/vo.txt` and give me a 20-second voiceover, calm female voice,
> save it as `vo.wav`.

> Add 15 seconds of chill lo-fi background music to the intro of my podcast
> episode, then tell me where you saved it.

> Make a 5-second 9:16 clip of the camera slowly orbiting our product render.

**Understanding files and links**

> What's in this whiteboard photo from the architecture review — `img_0421.jpg`
> — and how does it differ from the ER diagram I'm attaching?

> Summarize the key findings in `report.pdf` and list every table with its page
> number.

> Give me the tl;dw of this talk with timestamps:
> https://youtu.be/dQw4w9WgXcQ

**Transcripts and captions**

> I recorded a 40-minute all-hands on Zoom — give me an SRT file so I can put
> captions on the internal wiki.

> Fix the speaker labels in `call.wav` and export both a markdown transcript and
> SRT.

**Second opinions and code review**

> Before I show this deck to the client, get a second opinion on the pitch
> narrative — ask it to critique slide by slide (`deck.pdf`).

> Review the retry logic in `src/retry.py` and tell me whether the backoff can
> deadlock.

**Background work**

> Dig into how EU right-to-repair legislation affects refurbishers and come
> back with a sourced report. I'm stepping away — don't block on it.

> Research the current state of solid-state battery recycling and hand me the
> report when it's done.

What happens under the hood: the agent reads `SKILL.md`, picks the intent
command (`image`, `tts`, `analyze`, `transcribe`, `agent run`, …), dry-runs
unfamiliar calls, captures the artifact path or interaction ID from stdout, and
keeps building with it.

## Requirements

- `gemini-api` CLI v0.4+ on `PATH`
- Network access to the Gemini API
- `GEMINI_API_KEY` (env var, OS keychain, or `gemini-api configure`)

Check any time with `bash scripts/check_setup.sh` (exit 0 ready · 1 missing
binary · 2 auth). It never installs anything itself.

## Install

Any agent that supports Agent Skills can consume this directory as-is.

```bash
# Claude Code, Codex, Cursor, and other agents supported by vercel-labs/skills
npx skills add rajivmehtaflex/power-utility --skill gemini-api-cli

# Manual (Claude Code, user-wide)
cp -r dev-workspace/gemini-api-cli ~/.claude/skills/

# Manual (project-scoped)
cp -r dev-workspace/gemini-api-cli <project>/.claude/skills/
```

For agents that read an instruction file (`AGENTS.md`, `GEMINI.md`), point at
the skill instead of copying it:

```markdown
Skills live in dev-workspace/. Before generating media, transcribing, or
launching background research, read dev-workspace/gemini-api-cli/SKILL.md.
```

## Validate

```bash
npx -y skills-ref validate dev-workspace/gemini-api-cli
```

## Evals

- `evals/evals.json` — three end-to-end task evals with assertions
  (hero image, background research, SRT captions).
- Description trigger tuning used a 20-query should/should-not-trigger set;
  the shipped description is the best held-out performer (58%).

## License

Apache-2.0 — see [LICENSE](LICENSE). The `gemini-api` CLI itself is a separate
project: https://github.com/google-gemini/gemini-api-cli
