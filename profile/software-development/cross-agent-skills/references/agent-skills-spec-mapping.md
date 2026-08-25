# Agent Skills Spec — Field & CLI Reference

Condensed from https://agentskills.io/specification and https://github.com/vercel-labs/skills

## Directory Structure

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files
```

## Hermes → Spec Frontmatter Migration

| Hermes field | Spec field | Notes |
|-------------|-----------|-------|
| `name` | `name` (top level) | Same, but must match repo/dir name for npx |
| `description` | `description` (top level) | Expand with keywords, ≤1024 chars |
| `version` | `metadata.version` | Move into metadata map |
| `author` | `metadata.author` | Move into metadata map |
| `license` | `license` (top level) | Stays at top level |
| `tags: [a, b]` | `metadata.tags` | Move into metadata as string or list |
| (none) | `compatibility` | New — declare target agents + env reqs |
| (none) | `allowed-tools` | New — space-separated tool names |

## Spec Frontmatter Constraints

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | 1-64 chars, `[a-z0-9-]` only, no leading/trailing/double hyphens |
| `description` | Yes | 1-1024 chars, non-empty |
| `license` | No | Short license name or reference to LICENSE file |
| `compatibility` | No | 1-500 chars if provided |
| `metadata` | No | Map of string→string |
| `allowed-tools` | No | Space-separated, experimental |

## npx skills add — Full CLI Reference

Source: https://github.com/vercel-labs/skills

```
npx skills add <source> [options]
```

### Source Formats
- `owner/repo` — GitHub shorthand
- Full URL — `https://github.com/owner/repo`
- Local path — `/path/to/skills-dir`

### Options

| Flag | Description |
|------|-------------|
| `-g, --global` | Install to user directory instead of project |
| `-a, --agent <agents...>` | Target specific agents (claude-code, codex, antigravity, etc.) |
| `-s, --skill <skills...>` | Install specific skills by name (`*` for all) |
| `-l, --list` | List available skills without installing |
| `--copy` | Copy files instead of symlinking |
| `-y, --yes` | Skip confirmation prompts |
| `--all` | Install all skills to all agents |

### npx skills use

Generate a prompt for a skill without installing, or start a supported agent:

```bash
npx skills use owner/repo-name -s skill-name           # print prompt
npx skills use owner/repo-name -s skill-name --agent codex  # start codex
```

## Per-Agent Feature Matrix

| Feature | Claude Code | Codex | Antigravity | Cursor | Cline | OpenCode | OpenHands |
|---------|-------------|-------|-------------|--------|-------|----------|-----------|
| Basic skills | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `allowed-tools` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `context: fork` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Hooks | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |

## Progressive Disclosure

Agents load skills in three tiers:

1. **Metadata (~100 tokens):** `name` + `description` loaded at startup for ALL skills
2. **Instructions (<5000 tokens recommended):** Full SKILL.md body loaded when skill activates
3. **Resources (as needed):** Files in `scripts/`, `references/`, `assets/` loaded only when required

Keep SKILL.md under 500 lines. Move detailed reference material to separate files.
