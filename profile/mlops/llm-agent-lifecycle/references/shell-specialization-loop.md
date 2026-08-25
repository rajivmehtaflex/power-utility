# Shell Specialization Loop — External Probe to Student Training

Use this reference when a user wants to turn a smaller base model into a domain specialist using a Pi shell benchmark and a larger teacher model.

## Correct stage boundary

A benchmark is Stage 0 instrumentation, not a distillation or GRPO trainer:

```text
external Stage-0 probe
  -> repeated, machine-verified weakness profile
  -> teacher generates verified examples around confirmed weak labels
  -> trainable student receives response-level SFT/distillation
  -> optional GRPO in the real Pi harness with unaided attempts
  -> identical holdout probe + general regression suite
  -> export/deploy
```

The probe is aligned with the specialization objective only when its results drive the
next stages. A 60-item diagnostic set should steer a larger teacher-generated dataset;
do not reuse the entire diagnostic set as both training data and final evaluation.

## External-only evaluation mode

If the user says not to evaluate Ollama or generated scripts on the current machine:

1. Export public model-facing prompts separately from private fixture/verifier data.
2. Run the target model and scripts in a separate disposable evaluator.
3. Collect one JSONL record per `(session_id, track, case_id, attempt)`.
4. Import and validate records locally without invoking Ollama, Pi, Bash, or the sandbox.
5. Generate the weakness report from validated execution metadata only.

The importer must reject unknown case IDs, duplicate attempts, incomplete execution
objects, and unsupported tracks. It must never execute the model response during import.

## What makes a weakness credible

Do not infer a weakness from one wrong answer. Require a repeated pattern:

- multiple failed cases in one category, or repeated failure of one case across attempts;
- machine-verifiable functional, runtime, safety, or portability evidence;
- protocol failures (`no_code_block`, refusal, ambiguous fences) separated from capability;
- evaluator failures (`sandbox-unavailable`, fixture setup errors) excluded from capability rate;
- enough observations for a confidence statement (`insufficient`, `tentative`, `supported`).

Report category × difficulty, failure-label counts, pass@1/pass@N, and raw-versus-tool-track
gaps. Student-weak + teacher-strong is a high-value distillation target; if both are weak,
fix the task, verifier, or teacher before creating training data.

## Teacher-data rules

Use the teacher as a frozen reference/data generator or as a judge of an unaided student
attempt. Verify every teacher-generated solution with the same hidden checks. For each
confirmed weak label, generate varied examples covering basic behavior, edge cases,
negative cases, and alternative correct strategies.

If the teacher endpoint returns text only, call the result response-level distillation or
verified SFT. True soft-label/logit distillation requires teacher and student logits from
trainable checkpoints and a tokenizer-alignment strategy; an Ollama/GGUF text response is
not evidence of logit distillation.

## GRPO anti-pattern

Never let the student call the teacher as a live co-pilot during GRPO. That trains
runtime delegation, collapses group reward variance, and leaves the teacher capability
outside the student weights. A teacher judge that scores an unaided attempt is safe;
a teacher that supplies the solution during the attempt is not.

A Pi extension can provide prompts, fixtures, verifiers, result import, and reporting, but
it is not automatically a GRPO trainer. Token/action capture, rollout groups, advantages,
KL/reference handling, checkpoint training, and inference-weight synchronization require a
TRL/OpenEnv or custom training adapter.

## Feasibility and evaluation gates

A smaller specialist is achievable as a domain tradeoff, not as a general-purpose “God
model.” Compare:

```text
base 9B -> distilled 9B -> GRPO-sharpened 9B -> 27B teacher
```

Use the same unseen holdout plus a general regression set at every gate. Keep some general
training data and a reference/KL constraint to reduce catastrophic forgetting. A successful
result means materially better shell/Pi behavior at lower cost, not parity with the teacher
on every domain.
