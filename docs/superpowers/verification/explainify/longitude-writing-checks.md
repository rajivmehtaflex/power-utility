# longitude-asd-ste100 — verification checks (case C3, writing format)

Run directory: `explainify-output/longitude-writing-20261003-083214/` (repo `power-utility`,
branch `main`, uncommitted tree). Produced 2026-10-03. Format: `asd-ste100` (STE-inspired,
approximate). Checked in the profile's self-check order (meaning → mechanism/example →
terminology → sentence structure); a later check never overrides an earlier failure.

## Provenance (Step 1)

| Field | Value |
|---|---|
| source kind | `file` (UTF-8 `.md` file input) |
| requested_location | `/tmp/c3-fixture.md` |
| resolved_location | `/tmp/c3-fixture.md` |
| source_title | "Finding longitude at sea" (the fixture's own H1) |
| retrieval_status | `not-applicable` |
| retrieved_at | `null` |

- `retrieval_status` rationale: the file was read locally, in full, with no retrieval step.
  The schema's `retrieval_status` describes how much of a *retrieved* source was obtained,
  and `retrieved_at` is defined for *web* material. `cases.md` §2(a) prescribes
  `not-applicable` for the analogous fully-supplied pasted-text case; the same reasoning is
  applied to a fully-read local file. The file's complete content (1,505 bytes) was used;
  nothing was partial.
- The file is a **frozen evaluation fixture** inlined in
  `docs/superpowers/verification/explainify/cases.md` case C3, not a live user file. The
  materialized copy at `/tmp/c3-fixture.md` is byte-identical to the frozen block
  (`diff` clean against `cases.md` lines 82–106). A copy is stored at
  `docs/superpowers/verification/explainify/longitude-fixture.md`.
- **SHA-256:** `9f3ad6bb60ec76ba5a2735cddc20b7f5d119b35155fd7c66f2bd38a31b703aae`
- Audience: a curious reader unfamiliar with the story. Scope: the fixture's core story —
  the 1714 prize context, the longitude problem, Harrison's sea clock (1761 test, 1773
  recognition), the "does not depend / may vary" qualifications.
- Claim origins: every factual claim in the deliverable carries `origin: provided-source`;
  nothing from outside the fixture was added.

## Preserved-elements table (side by side)

| # | Fixture phrase | Output phrase (`longitude-asd-ste100.md`) | Class | Preserved |
|---|---|---|---|---|
| 1 | "In 1714 the British Parliament passed the Longitude Act" | "In 1714, the British Parliament passed the Longitude Act." | date | Yes |
| 2 | "H4, sailed toward Jamaica in 1761" | "H4 sailed toward Jamaica in 1761." | date | Yes |
| 3 | "payments continued in stages until 1773" | "Payments continued in stages until 1773." | date | Yes |
| 4 | "they could not find their longitude at sea reliably" | "they could not find their longitude at sea reliably" | negation | Yes |
| 5 | "it was never convenient for every navigator" | "it was never convenient for every navigator" | negation | Yes |
| 6 | "the Board of Longitude did not pay the largest reward at once" | "the Board of Longitude did not pay the largest reward at once" | negation | Yes |
| 7 | "the watch method does not depend on the weather" | "the watch method does not depend on the weather" | negation | Yes |
| 8 | "is still not known" | "is still not known" | uncertainty | Yes |
| 9 | "the performance may vary with oil, temperature, and care" | "The performance may vary with oil, temperature, and care." | uncertainty | Yes |
| 10 | "which was probably its decisive advantage" | "This advantage was probably decisive." | uncertainty | Yes |
| 11 | "find longitude within half a degree at the end of a voyage to the West Indies" | "find longitude within half a degree. The test condition was the end of a voyage to the West Indies." | condition | Yes |
| 12 | "one hour of difference equals fifteen degrees" | "One hour of difference equals fifteen degrees." | mechanism | Yes |
| 13 | "a carpenter and self-taught clockmaker, built sea watches instead" | "John Harrison was a carpenter and a self-taught clockmaker. He built sea watches instead." | claim | Yes |
| 14 | "the recorded error of the trial was small enough to meet the Act's condition" | "The recorded error of the trial was small. It was small enough to meet the Act's condition." | claim | Yes |

Coverage: 3 dates (rows 1–3), 4 negations (rows 4–7), 3 uncertainty markers (rows 8–10) —
meets and exceeds the required ≥3 dates, ≥3 negations, ≥2 uncertainty markers.

## Self-check results (in order)

1. **Meaning and qualifications preserved — PASS.** All three dates, all four negations,
   all three uncertainty markers, the half-a-degree condition, and the one-hour/15-degrees
   rule survive verbatim or near-verbatim (table above). The uncertainty was NOT flattened:
   the output never says "H4 was accurate"; it keeps "still not known" and "may vary".
   Tense: historical events stay past tense ("passed", "sailed", "continued", "worked");
   the general mechanism stays present tense ("needs", "equals", "reads", "acts",
   "does not depend"). Past was not converted to present.
2. **Mechanism and example consistency — PASS.** The mechanism chain in the output matches
   the fixture's recipe in order: find latitude vs longitude (problem) → longitude needs the
   time difference between ship and reference meridian → one hour = fifteen degrees →
   keep time at sea, compare with the reference meridian, turn the difference into degrees.
   No worked numeric example is used in the writing deliverable, so no arithmetic to check;
   the single quantitative rule (1 h = 15°) is quoted as stated by the source.
3. **Terminology consistency — PASS.** `latitude`, `longitude`, `reference meridian`,
   `lunar distances`, `sea watches`/`watch method`, `timekeeper` (H4) are each used in one
   sense; no synonym-hopping between "clock"/"watch"/"timekeeper" for the same referent
   beyond the fixture's own naming (H4 is a "timekeeper"/"sea watch"; the method is the
   "watch method", matching the fixture's term). Referents are explicit; no bare "it".
4. **Sentence structure and readability — PASS.** 33 prose sentences, 274 words, mean 8.3
   words/sentence, maximum 16 words; 0 sentences over the 20-word target, so no accuracy
   exceptions were needed. One idea per sentence throughout.

## Sentence stats

- Sentences: 33. Words: 274. Mean: 8.3. Median: 7. Max: 16 ("How closely H4 would have
  kept time over decades of ordinary service is still not known."). Over 20 words: 0.
- Distribution (words/sentence): 3, 4, 5×3, 6×6, 7×3, 8×3, 9×7, 10×3, 11, 12×2, 13, 14, 16.

## Limitations of this check

- Meaning preservation was verified by side-by-side comparison of the deliverable against
  the frozen fixture by the producing agent; no second independent reviewer or automated
  semantic check ran.
- The 20-word target is this project's profile choice, not an official STE rule; passing it
  implies no ASD-STE100 conformity (per the profile label on the deliverable).
