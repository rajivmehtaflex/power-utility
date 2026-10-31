---
name: rust-to-python-bridge
description: Use when a user requests Rust functionality callable from Python, asks to add or extend a Python/Rust FFI, or wants to assess whether a task fits an existing Rust extension.
license: MIT
compatibility: Requires an agent with file access and terminal command execution. Study, feasibility, and environment-preflight steps are read-only. Implementation requires the project's Rust toolchain (cargo) and a Python interpreter; network access is only needed if build dependencies are not already cached locally.
metadata:
  author: rajivmehtapy
  version: "1.0.0"
---

# Rust to Python Bridge

Use this skill for `$rust-to-python-bridge <Task>`. Treat Python as the caller-facing API and put the requested native work in Rust when the codebase and task make that a sound fit.

## Required workflow

1. **Study the active codebase.** Read applicable repository instructions and inspect the relevant Python callers, Rust code, binding exports, packaging/build configuration, type declarations, and tests. Use CodeGraph before text search when the repository is indexed and CodeGraph is available. Do not assume paths, libraries, or conventions from another project.
2. **Assess feasibility and environment before editing.** Follow [discovery and feasibility](references/discovery-and-feasibility.md), then perform the mandatory [environment preflight](references/environment-preflight.md) against the discovered requirements, including for existing bridges. Use read-only terminal checks that work without a GUI. Do not edit implementation files, install dependencies, trigger toolchain downloads, run generators or builds, or create project files during this assessment.
3. **Report and pause.** Present the feasibility status, environment readiness with evidence and any proposed setup commands, the existing design pattern, a proposed Rust responsibility and Python API, affected areas, dependencies, risks, and acceptance checks. Ask for approval of that proposal and wait. A request to implement the task does not skip this checkpoint.
4. **Implement only the approved scope.** Follow [bridge patterns](references/bridge-patterns.md) and [implementation and verification](references/implementation-and-verification.md). If new findings materially change the approved API, architecture, dependencies, or scope, report the change and wait for approval again.
5. **Report completion.** Explain how Python calls the Rust implementation, what changed, which checks ran and their results, and any remaining limitations. Make no performance or zero-copy claim without evidence.

If Rust is infeasible or does not offer a credible benefit for the requested workload, say why and offer practical alternatives. Do not silently replace the requested Rust implementation with a Python-only implementation.

## References

- [Discovery and feasibility](references/discovery-and-feasibility.md)
- [Environment preflight](references/environment-preflight.md)
- [Bridge patterns](references/bridge-patterns.md)
- [Implementation and verification](references/implementation-and-verification.md)
