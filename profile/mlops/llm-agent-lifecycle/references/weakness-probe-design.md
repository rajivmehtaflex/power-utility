# Designing a domain weakness probe (when standard benchmarks don't cover it)

Custom capability-probe pattern distilled from the git-distill Stage-0 eval
(`pi-local-dev/packages/pi-shell-benchmark`, 2026-08). Use when a model must be measured in
a domain no harness task covers (e.g. shell-script generation for bash 3.2/BSD) and the
result must steer *training data*, not just report a score.

## When to build a probe instead of using lm-eval-harness

- The domain is specific (a bash dialect, an internal DSL, a tool protocol) — no standard
  harness task exists.
- The consumer of the result is a training pipeline (distillation prompt mix / GRPO task
  set), so the output must be a *profile*, not a single number.
- Tasks are executable and machine-verified. Never use opinion/LLM-judge questions — they
  measure vibes, are unreproducible, and re-runs drift.

## Design checklist

1. **Category × difficulty grid** — 6–10 categories × 3 tiers × ~6–8 items (60 total works
   well). One overall score steers nothing; the grid localizes the weakness.
2. **Executable fixtures** — every item = prompt + `setup` script + `verify` script
   (file-based checks only: `test`, `grep -Fxq`, `wc -l < f | tr -d ' '`). Difficulty 3 =
   the category's classic trap (subshell-lost counters, BSD-vs-GNU `sed -i`, unset var
   under `set -u`, literal glob in a variable, `while read` final line without newline).
3. **Failure-mode taxonomy** — functional / timeout / output-format / safety-block /
   sandbox. Heavy `output-format:*` failures mean a harness bug (model format quirk, e.g.
   thinking models emitting multiple fences), not model weakness — fix the harness, don't
   train against it.
4. **Determinism** — temperature 0 + fixed seed; borderline items flip run-to-run, so treat
   per-category aggregates as the signal unit, not single cases.
5. **Sandbox** — fresh mkdtemp cwd + hard timeout + destructive-pattern scan that BLOCKS
   (not warns) before execution. Generated code runs by design; network commands and
   `sudo`/`rm -rf /`/`dd`/`mkfs` patterns must be hard-blocked pre-spawn.
6. **Pin the dialect** — macOS bash 3.2/BSD vs GNU is a real measured variable, not a
   confound to hide. Decide the deployment dialect before Stage-1 training and record it
   in the profile. (Honor a `BENCH_SHELL`/`shell` field per run.)
7. **Teacher-ceiling control** — run the identical rubric against the teacher tier:
   student-weak ∧ teacher-strong = highest-yield distillation targets; teacher-weak = wrong
   teacher or bad verification data.
8. **Two tracks when agentic** — raw (model writes a script cold, no tools) vs harness
   (model works inside the agent loop with tools). The per-category track gap separates
   syntax weakness from agentic weakness and routes training data accordingly.
9. **Weakness profile → data mix** — weak categories get ≥ 50% of the Stage-1 distillation
   prompt mix; over-sample the difficulty tiers where failures cluster. The rubric doubles
   as the Stage-2 GRPO task/reward set — one asset feeds both stages.
10. **Re-run for proof** — the same probe command before/after training is the
    specialization evidence.

## Pipeline placement (why the probe exists at all)

Distillation copies the teacher's distribution on whatever prompts you choose; GRPO
sharpens on whatever tasks you choose. Neither can target weaknesses that were never
measured. Ordering is forced: **distill first (only stage that changes size) → GRPO
second (sharpen, source=target) → export**. The probe is Stage 0 and its rubric is the
Stage-2 seed task set. Technique-level distinctions and anti-patterns: see
`references/distill-vs-grpo-pipeline.md` (sibling reference in this skill).

## Concrete instance

`pi-local-dev/packages/pi-shell-benchmark` — 60 cases, 8 categories, two tracks
(raw / pi-tools), 5 scoring dimensions (45/20/20/10/5), TypeScript with zero runtime npm
deps, contract-first (the failing tests defining `sandbox.ts`/`scoring.ts`/`invoker.ts`
shipped before those modules existed). Ollama-backed raw track
(`http://localhost:11434/api/chat`, temp 0 seed 42); pi-tools track spawns
`pi --mode text --no-session --no-context-files --model <m> --tools read,write,edit,bash -p`
and refuses to run without a declared external sandbox.
