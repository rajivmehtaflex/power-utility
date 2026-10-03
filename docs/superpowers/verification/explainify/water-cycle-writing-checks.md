# C4 (writing half) — checks for `water-cycle-asd-ste100.md`

Run: `explainify-output/water-cycle-writing-20261003-083029/` (2026-10-03). Case: C4
writing half of §9 evaluation — same frozen pasted water-cycle paragraph as the C4
video run, produced under the `asd-ste100` writing format. Checked against SKILL.md
Step 4 teaching checks, the writing profile rules in
`repo-owned/explainify/references/asd-ste100.md`, and the C4 expected evidence in
`docs/superpowers/verification/explainify/cases.md`.

## 1. Preserved-phrases table (side by side)

| # | Fixture phrase (frozen C4 text) | Output wording | Preserved element | Status |
|---|---|---|---|---|
| 1 | "it does not have a starting point" | "The cycle does not have a starting point." | negation | preserved |
| 2 | "it is never perfectly closed" | "The cycle is never perfectly closed, because water can stay stored in ice and underground for long periods." | negation | preserved |
| 3 | "fall as rain or snow" | "Heavy drops then fall as rain or snow." | disjunction (both outcomes kept) | preserved |
| 4 | "Some of this water soaks into the ground, and some flows back to the ocean in rivers." | "Some of this water soaks into the ground. Some water flows back to the ocean in rivers." | partial split ("some … and some …") | preserved (split into two sentences, both branches kept) |
| 5 | "water can stay stored in ice and underground for long periods" | "water can stay stored in ice and underground for long periods" | condition + duration ("can", "for long periods") | preserved (near-verbatim) |
| 6 | causal link "… never perfectly closed, because water can stay stored …" | same sentence retained in one output sentence | cause attached to qualification | preserved (not split) |

Counts: 5/5 must-preserve phrase groups preserved (negations 2/2, disjunction 1/1,
partial split 1/1, storage duration 1/1); 1 causal link additionally preserved.

## 2. Central-claims check

- Water moves between oceans, air, and land — present (sentence 1).
- Sun heats oceans and lakes; water becomes vapor and rises — present (sentences 3–4).
- Colder air higher up; vapor becomes tiny drops; drops form clouds — present
  (sentences 5–7).
- Drops join, become heavy, fall as precipitation — present (sentences 8–9).
- Water soaks into ground AND flows back via rivers — present, both branches
  (sentences 10–11).
- Cycle repeats, with both closing qualifications — present (sentences 12–14).
- No claim was added beyond the source: zero model-knowledge statements, zero
  invented citations, zero numerical additions. Attribution block records
  `kind: text`, fixture provenance, `retrieval_status: not-applicable`.

## 3. Sentence statistics (prose sentences of "The explanation" section)

14 prose sentences; per-sentence word counts: 10, 6, 6, 9, 6, 10, 4, 7, 8, 8, 9, 6, 8,
18. Maximum 18 words, mean 8.2 words, **0 sentences over the 20-word target** — no
exceptions to report. Quotation material in the limitations section and the
attribution list were assessed separately per the profile, not counted as prose.
Sentence 14 (18 words) was deliberately kept as one sentence so the "because" cause
stays attached to the "never perfectly closed" negation.

## 4. Self-check order (per references/asd-ste100.md)

1. Meaning and qualifications preserved — pass (table above; dates/negation/uncertainty
   N/A for this fixture except its negations and conditions, all kept).
2. Mechanism consistency — pass (ordered causal chain intact: heating → vapor → rise →
   cooling → drops → clouds → join/heavy → precipitation → soak/runoff → repeat).
3. Terminology consistency — pass ("vapor" defined before first use, then used
   consistently; "water cycle", "drops", "cycle" each used one way; no synonyms
   alternated).
4. Sentence structure and readability — pass (one main idea per sentence; explicit
   referents; ≤20 words everywhere).

## 5. Format and delivery checks

- Profile label present and exact: "STE-inspired simplified English — approximate, not
  validated for ASD-STE100 conformity" — no ASD-STE100 conformity or certification
  claim anywhere in the file.
- Structure follows the delivered-document order: profile label → explanation → source
  attribution → material scope limitations; no internal checklist dump in the
  deliverable.
- Fresh run directory `water-cycle-writing-20261003-083029/` under
  `./explainify-output/`; nothing overwritten; installed skill files untouched.
- No video tool was invoked for this writing run (no `uv`, `ffmpeg`, `ffprobe`);
  evidence for C8(a). `python3` was used once, after the deliverable existed, only to
  compute the sentence statistics above — verification tooling, not a writing
  dependency.
