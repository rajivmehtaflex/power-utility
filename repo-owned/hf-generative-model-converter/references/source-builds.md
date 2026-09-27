# Source builds — preflight, policy, and workspace lifecycle

Applies to every converter/runtime native component this skill builds. Governing rule: **no silent
prebuilt binaries.** Converter/runtime code (llama.cpp today) and its native dependencies are pinned
and built locally; an unannounced binary arriving through pip, CMake/FetchContent, Bazel, a container,
or Git LFS is a violation, not a convenience. Declared system inputs (interpreter, compiler/linker,
CMake/Ninja, OS C library, drivers/SDKs) are recorded with versions and origin but not rebuilt.

## Preflight (run before any build; abort the route if unsatisfied)

1. CPU count and features, effective memory limit, free writable disk on the workspace mount.
2. Compiler/linker/CMake presence and versions; record them with the build.
3. Accelerator visibility — absence of a device is a fact to record (CPU-only), never a silent fallback after assuming one.
4. Space + peak-memory estimate for the build, labeled known or unknown; cap jobs to CPU count and memory headroom.

## Workspace layout (git-ignored, per user project)

```
<user-project>/.hf-converter/
├── sources/<component>-<rev>/     # pinned checkouts (immutable; refetch rather than mutate)
├── builds/<build-key>/            # CMake build trees; incomplete builds carry no READY marker
├── envs/<build-key>/              # UV-managed Python envs pinned per build
└── runs/<run-id>/{work,stage,logs}  # one conversion/validation attempt; local receipts kept beside stage
```

`build-key` = hash over: component source + submodule revisions, dependency-lock hash, compiler/ABI id,
build flags, target architecture, and relevant SDK versions. A build may be reused only when the key
matches **and** the runtime passes its health check (`llama-cli --version` and a minimal generation).

Changing any of: model revision, recipe, profile, toolchain, or artifact bytes → invalidate the affected
conversion/validation results. Never erase unrelated files or healthy caches to recover a failed run;
preserve logs and stop that route instead.

## Declared system inputs for this baseline (recorded at P2 preflight, see feasibility.md)

| Input | Version | Origin |
|---|---|---|
| gcc / g++ | 13.3.0 | Ubuntu 24.04 apt |
| make / cmake | 4.3 / 3.28.3 | Ubuntu 24.04 apt |
| libcurl (runtime + dev headers) | 8.5.0 / 8.5.0-2ubuntu10.15 | Ubuntu 24.04 apt (installed 2026-09-27 for `LLAMA_CURL`) |
| git / curl | 2.42.0 / 8.5.0 | Ubuntu 24.04 apt |
| Python | 3.12.3 | system |
| uv | 0.11.18 | standalone installer |
| GPU driver / SDK | none | no accelerator present — CPU baseline |

## Binary policy during Python converter envs

- Python-only packages: pinned versions resolved into `envs/<build-key>/` with the exact lock recorded.
- Any pip wheel that ships a compiled artifact touching the conversion path must be either rebuilt from
  pinned source or explicitly recorded as a named binary exception with user authorization. Optional
  native Hub transfer extensions are inspected for this before use.
- Heavy builds run sequentially (this host: `-j4`) unless measured headroom says otherwise.

## Download rules

- Model/tool sources resolve to immutable revisions; resumable upstream APIs only.
- Shard indexes and required files are checked before a load is attempted.
- Interrupted transfers resume; a completed download is content-verified before reuse.
