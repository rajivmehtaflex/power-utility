# gemini-api-cli

Cross-agent [Agent Skill](https://agentskills.io/specification) for the Google
`gemini-api` CLI — text, images, voice, music, video, file/YouTube analysis,
transcription, and background managed agents.

## Requirements

- `gemini-api` CLI v0.4+ on `PATH`
- Network access to the Gemini API
- `GEMINI_API_KEY` (env var, OS keychain, or `gemini-api configure`)

Check any time with `bash scripts/check_setup.sh` (exit 0 ready · 1 missing
binary · 2 auth).

## Install

Any agent that supports Agent Skills can consume this directory as-is.

```bash
# Claude Code, Codex, Cursor, and other agents supported by vercel-labs/skills
npx skills add rajivmehtaflex/power-utility --skill gemini-api-cli

# Manual (Claude Code)
cp -r dev-workspace/gemini-api-cli ~/.claude/skills/

# Manual (project-scoped, any agent)
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
  the shipped description is the best held-out performer.

## License

Apache-2.0 — see [LICENSE](LICENSE). The `gemini-api` CLI itself is a separate
project: https://github.com/google-gemini/gemini-api-cli
