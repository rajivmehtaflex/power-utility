# Distill-vs-GRPO: technique boundaries and pipeline anti-patterns

Reference for the shrink-then-sharpen model-specialization pipeline. Source: user's
"Shrinking a 27B Model Into a Coding Agent" field guide (2026-08), studied as ground truth
for the git-distill project (Ridge-27B teacher → Qwen3.5-9B student).

## The two techniques are different knobs

| | GRPO (sharpen) | Distillation (shrink) |
|---|---|---|
| Source vs target | Same model, same size | Two models, different sizes |
| Learning signal | Reward from its own group of attempts | Match teacher's soft-label distribution (KL) at every token |
| Verifier needed | Yes — hidden tests, pass/fail | No — needs a frozen teacher instead |
| Changes model size | No — structurally cannot | Yes — that is the entire point |
| Data appetite | Dozens–hundreds of reward tasks | Tens–hundreds of thousands of teacher outputs |
| Big-model placement | As a judge scoring unaided attempts | As the teacher, directly |

## GRPO mechanics in one pass

Group of N attempts from same weights → hidden-test scores → advantage = (score − group
mean)/group std (group is its own baseline; no critic network) → credit only action tokens
(not thinking tokens) → KL leash to frozen reference copy → nudge existing weights (never
add/remove) → sync rollout server → repeat. Reward curve compounds (demo: 0.27 → 0.71 over
10 steps). GRPO does NOT reset or retrain: pretraining stays intact; it makes latent good
behavior more consistent. The leash only makes sense because nothing starts over.

## Distillation mechanics

Large frozen teacher + small student (started from a competent small base, not random).
Same prompt to both; student trained to match teacher's full next-token probability spread
("soft labels" — 70% B / 20% C / 10% A carries information a hard label throws away).
Only student weights move. Result: smaller, faster, not-identical copy; capability gap
depends on data quality/volume.

## Forced pipeline ordering

1. **DISTILL (shrink)**: 27B teacher generates across many prompts → small base trained on
   soft labels → ~9B student (ordinary independent model).
2. **GRPO (sharpen)**: student runs in a real agent harness in sandboxes, scored on hidden
   tests; source = target, same model.
3. **EXPORT/DEPLOY**: GGUF or HF export → run where the small model needs to live.

Distill first because it is the only stage that can change size. GRPO-then-distill just
distills from an already-sharpened big model without solving size any earlier.

## Anti-patterns (each has killed a real plan)

- **"Train the 27B and an 8B pops out"** — impossible in one step. Gradient descent only
  turns existing dials; it cannot add or remove parameters. Same-size-in/same-size-out is
  structural, not a design choice.
- **Training a GGUF** — GGUF is quantized, inference-only; backprop needs original PyTorch
  weights. Convert/pull the HF checkpoint instead.
- **Live oracle inside the GRPO loop** (small model may call a big model mid-task when
  stuck): (a) collapses the group's reward spread → advantage calc starves (every attempt
  succeeds regardless of the trainee's own behavior); (b) reinforces *delegating*, not
  reasoning — GRPO only reinforces tokens the trainee produced; (c) trains a deployment
  environment habit the shipped model can't support, leaving it worse standalone than if
  never trained. Fix is placement, not abstinence: big model as Stage-1 teacher (transfers
  into weights permanently) or as judge scoring unaided attempts (adds signal, no offload)
  — never a co-pilot inside the loop.
- **Reward-hacking blind spot** — two different failure modes can score identically (zero)
  (never ran the code vs. timed out); matters for reward-function design, not the math.

## Harness notes (Pi as GRPO harness)

Recipe is harness-agnostic in principle: any sandboxed agent talking to the model over a
capturable API qualifies. Pi (small core + extension API) is a named roadmap target and a
plausible substitute — benchmarked as context-efficient per turn (good for RL economics,
transfer unproven). Today a harness swap means hand-writing: token-capture adapter,
filtering harness housekeeping calls out of training, matching tool-call format to the
inference server. Promising, not drop-in.

## Compressed rule

Shrink first, sharpen second — and borrow intelligence into the **weights**, not into the
**runtime**.
