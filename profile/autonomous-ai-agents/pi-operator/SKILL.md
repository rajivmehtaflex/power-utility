---
name: pi-operator
description: Operate and verify the Pi coding-agent CLI safely.
license: MIT
metadata:
  author: Hermes
  hermes_tags: Pi, CLI, CodingAgent, Sessions, Packages
  platforms: macos, linux
  version: 0.1.0
---

# Pi CLI Operator

Use this skill to operate and verify the `@earendil-works/pi-coding-agent` CLI: inspect its local help, choose an execution mode, manage sessions and Pi packages, control tools, and check provider readiness. It does not write project code or expose credentials unless the user explicitly requests credential export; invoke commands through the Hermes `terminal` tool and treat the installed executable's help as the version-specific contract.

## When to Use

- The user asks how to use `pi` or requests `pi --help` analysis.
- The user wants an interactive, one-shot, JSON, or RPC Pi invocation.
- The user needs session resume, fork, export, or naming guidance.
- The user needs Pi package install, removal, update, listing, or resource configuration.
- The user needs provider/model authentication readiness checks.
- The user asks for a read-only review or tool-restricted Pi run.
- The user asks to reconcile installed CLI help with official Pi documentation.

## Prerequisites

- The `pi` executable must already be installed.
- Verify that the shell can resolve `pi`; for a Bun user-local install, prepend `$HOME/.bun/bin` when needed.
- Provider authentication is required for model calls. Use `/login`, provider environment variables, or Pi's auth storage; do not print secrets unless explicitly requested.
- Optional documentation comparison requires the Exa MCP server (`mcp__exa__web_search_exa` and `mcp__exa__web_fetch_exa`).

## How to Run

Invoke Pi through `terminal` from the target project directory. Start with `pi --version` and `pi --help`; use the local help output to confirm flags before applying version-sensitive commands. For a Bun user-local installation, pass `export PATH="$HOME/.bun/bin:$PATH"` in the same `terminal` command when `pi` is not already on `PATH`.

## Quick Reference

Pass these command strings to `terminal`:

```bash
pi --version
pi --help
pi
pi "<initial request>"
pi @README.md "Summarize this file"
pi -p "<one-shot request>"
pi -p @README.md "Summarize this text"
pi --mode json -p "<request>"
pi --mode rpc --no-session
pi -c
pi -r
pi --session <path-or-id>
pi --session-id <id>
pi --fork <path-or-id>
pi --no-session
pi --name "<session name>"
pi --export session.jsonl output.html
pi --provider <provider> --model <model> "<request>"
pi --model <provider>/<model> "<request>"
pi --thinking high "<request>"
pi --models "<patterns>"
pi --tools read,grep,find,ls -p "<read-only request>"
pi --no-tools
pi --exclude-tools <tool>
pi --no-extensions -e ./my-extension.ts
pi install npm:@foo/bar
pi install npm:@foo/bar@1.2.3
pi install git:github.com/user/repo@v1
pi install ./local/path -l
pi remove npm:@foo/bar
pi uninstall npm:@foo/bar
pi update
pi update --self
pi update --extensions
pi update --models
pi update --all
pi update --extension npm:@foo/bar
pi list
pi config
pi config -l
pi auth check --provider <provider> --json --no-refresh
pi auth print-api-key --provider <provider>
pi auth print-bearer-token --provider <provider> --min-expiry <duration>
```

## Procedure

1. **Verify the installed CLI.** Invoke through `terminal`:
   ```bash
   export PATH="$HOME/.bun/bin:$PATH" && command -v pi && pi --version
   ```
   Completion criterion: `command -v` returns the intended executable and `pi --version` returns a version.

2. **Inspect the version-specific contract.** Invoke through `terminal`:
   ```bash
   export PATH="$HOME/.bun/bin:$PATH" && pi --help
   ```
   Then inspect subcommands with `pi install --help`, `pi remove --help`, `pi update --help`, `pi list --help`, `pi config --help`, and `pi auth --help`.
   Completion criterion: the requested flags and subcommand syntax appear in local help.

3. **Choose the least-privileged execution mode.** Use `pi -p` for one request, `--mode json` for event streams, `--mode rpc` for process integration, and `--tools read,grep,find,ls` for read-only review. Use normal interactive `pi` only when ongoing conversation or file changes are intended.
   Completion criterion: the selected mode matches the requested side effects and output format.

4. **Attach context correctly.** Use `@filename` arguments, for example:
   ```bash
   pi @README.md "Summarize this"
   ```
   In interactive mode, `@` searches files; `!command` sends shell output to the model and `!!command` runs without adding output to model context.
   Completion criterion: every intended file is represented by an `@` argument or interactive file selection.

5. **Control provider, model, and thinking.** Use `--provider`, `--model`, `--thinking`, and `--models`. A provider-prefixed model such as `--model openai/gpt-4o` does not require a separate `--provider` flag.
   Completion criterion: the chosen provider/model/thinking values are visible in the command or interactive `/model` selection.

6. **Manage sessions deliberately.** Use `-c` for the most recent session, `-r` to browse, `--session` for a known file or partial ID, `--session-id` for an exact project session ID, `--fork` to branch, `--no-session` for ephemeral work, and `--export` for HTML output.
   Completion criterion: the command either resumes, forks, creates, suppresses, or exports the intended session.

7. **Manage Pi packages separately from the global CLI installer.** Use `pi install`, `remove`, `list`, `config`, and `update` for Pi resources. Use `-l` for project-local settings. Use `pi update --models` for model catalogs; use `pi update --self` for Pi itself.
   Completion criterion: inspect `pi list` or the relevant settings scope after a package operation.

8. **Handle project trust explicitly.** Use `--approve` only when project-local settings/resources are trusted. Use `--no-approve` for untrusted or controlled non-interactive runs. Non-interactive modes do not show a trust prompt.
   Completion criterion: the trust choice is explicit in the command whenever project-local resources could be loaded.

9. **Check authentication without leaking secrets.** Prefer:
   ```bash
   pi auth check --provider <provider> --json --no-refresh
   ```
   Use `--credentials`, `print-api-key`, or `print-bearer-token` only when an external process explicitly needs the credential.
   Completion criterion: readiness is confirmed without credential material appearing in logs unless export was requested.

10. **Compare documentation only when version drift matters.** Use Exa MCP to fetch the exact version-tagged usage page and compare it with the current latest page. Treat the installed `pi --help` output as authoritative for accepted flags. Current documentation may contain flags absent from an older installation, such as `--use-theme`.
   Completion criterion: each reported discrepancy is labeled as local-only, version-tagged documentation, or latest-documentation behavior.

## Pitfalls

- Use `@README.md`, not `@file:README.md`; Pi's file-argument syntax is a leading `@` followed by the path.
- A Bun-installed Pi can be installed successfully but unavailable in an agent shell until `$HOME/.bun/bin` is added to `PATH`; verify in a fresh shell before reinstalling.
- The normal default tools include `read`, `bash`, `edit`, and `write`; use `--tools read,grep,find,ls` for a read-only run.
- Pi packages and extensions execute with substantial system access. Review third-party sources before `pi install`.
- Versioned npm specs and Git `@ref` sources are pinned; broad extension updates do not move them to a new ref.
- `pi update --models` refreshes model catalogs; it does not update the Pi executable.
- `pi config` opens a TUI; it is not a plain-text settings display. `Tab` switches between global and project-local scopes.
- `--approve` can enable project-local extensions, skills, prompts, and settings. Do not use it automatically in untrusted repositories.
- `pi auth print-api-key`, `pi auth print-bearer-token`, and `pi auth ... --credentials` emit sensitive data.
- The exact `v0.84.1` usage documentation omits `--session-id`, while the installed help exposes it. Prefer the executable help for local operation.
- The current latest documentation lists `--use-theme`, but the installed `0.84.1` help does not. Do not assume a latest-page flag exists locally.
- JSON and RPC modes are machine-oriented output modes; do not parse them as normal human-readable responses.

## Verification

Invoke through `terminal` and require exit code `0`:

```bash
export PATH="$HOME/.bun/bin:$PATH" && pi --version && pi --help >/dev/null && pi auth --help >/dev/null
```

Reference documentation: [Pi usage](https://pi.dev/docs/latest/usage), [Pi packages](https://pi.dev/docs/latest/packages), [Pi quickstart](https://pi.dev/docs/latest/quickstart), and the [v0.84.1 usage page](https://github.com/earendil-works/pi/blob/v0.84.1/packages/coding-agent/docs/usage.md).
