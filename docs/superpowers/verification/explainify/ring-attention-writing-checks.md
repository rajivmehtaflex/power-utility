# Ring attention — writing verification checks (`asd-ste100`)

Run directory: `explainify-output/ring-attention-writing-20261003-083306/`
(repo: `power-utility`, branch `main`, uncommitted tree). Case C1, PART A of the §9
evaluation suite. Deliverable checked: `ring-attention-asd-ste100.md`.

Checks were run in the reference's required order (meaning → mechanism/example →
terminology → sentence structure). A later check never overrides an earlier failure.

## Internal teaching brief (recorded for this run, not part of the deliverable)

- **source:** topic `ring attention`; no retrieval performed (`kind: topic`,
  `retrieval_status: not-applicable`); every claim origin `model-knowledge`, except
  layout-free qualitative comparisons which are still model-knowledge.
- **audience:** curious reader unfamiliar with the concept (default).
- **learning_objective:** understand what ring attention is and the one key mechanism —
  KV blocks travel around a device ring while queries stay local, so full attention is
  computed without any device holding the whole KV data.
- **prerequisites:** token, transformer, attention, query/key/value, device + memory —
  all introduced in "The parts you need first" before use.
- **terms:** token, transformer, attention, query, key, value, KV data, sequence shard,
  sequence sharding, KV block, device ring, partial attention result — each defined
  before first use, then used consistently.
- **core_claim:** ring attention splits a long sequence into shards spread across
  devices linked in a ring; queries stay home while KV blocks circulate, and after one
  loop every device has attended to the whole sequence without replicating the KV data.
- **must_preserve:** the negation "Attention itself is unchanged — only the arrangement
  of computation across devices changes"; the condition "This match holds in exact
  arithmetic" with the rounding qualification; no numerical/performance claims
  (qualitative size comparisons only); no invented citations.
- **omissions:** training/load-balancing, overlapping vs non-overlapping schedules,
  partial-result merge arithmetic, implementations/hardware/performance, causal masking.

## Check 1 — Meaning and qualifications preserved: PASS

- Negation survived: "Attention itself is unchanged — only the arrangement of
  computation across devices changes." and "Ring attention changes where attention is
  computed, not what attention computes." (no softening of either negation).
- Uncertainty/qualification survived: "This match holds in exact arithmetic." followed
  by "Real hardware rounds numbers, so tiny differences can appear." — the equivalence
  claim keeps its floating-point qualification instead of a flat "identical result".
- Conditions survived: "too large for one device" stays conditional on a very long
  sequence ("A very long sequence makes…"), not an absolute claim about every sequence.
- Attribution: "generated from model knowledge; no external source was retrieved", dated
  2026-10-03; no quotation marks around paraphrases; no fabricated citations.
- **No unsupported numerical or performance claims (the C1 guard):** the text contains
  no context-window multipliers, FLOPs, memory-savings percentages, throughput figures,
  device counts, or benchmark results. Every size statement is qualitative
  ("grows as the sequence gets longer", "too large for one device", "no single member
  could hold alone"). The only numbers in the file are the date 2026-10-03 and the
  standard's name ASD-STE100 — neither is a performance claim.

## Check 2 — Mechanism and example consistency: PASS

- The mechanism's causal order in the text matches ring attention: shard the sequence →
  one shard (its KV block) per device → devices linked in a ring → queries stay home →
  all devices pass their held KV block simultaneously (send to one neighbor, receive
  from the other) → visiting block is matched against local queries → values
  contributed by match strength → contribution added to a partial attention result →
  block moves on → after one full loop every device has seen every block → partial
  results merged into one attention output per query.
- No worked example with arithmetic is used, so there is no example arithmetic to
  check; the qualitative "one full loop" statement is consistent with every block
  visiting every device exactly once.
- No illustrative numeric values appear, so there is nothing to label illustrative.

## Check 3 — Terminology consistency: PASS

Defined before first use and then used one way (no synonyms rotated):

| Term | Defined at | Used consistently |
|---|---|---|
| token | "The parts you need first" | yes |
| transformer | "The parts you need first" | yes |
| attention | "The parts you need first" | yes |
| query / key / value | "The parts you need first" | yes |
| device | "The parts you need first" | yes |
| KV data | "The problem" | yes |
| sequence shard / sequence sharding | "The idea: shards and a ring" | yes |
| KV block | "The idea: shards and a ring" | yes |
| device ring | "The idea: shards and a ring" | yes |
| partial attention result | "The mechanism" | yes |

Referents are explicit ("The visiting block", "that loop", "its other neighbor"); no
bare "it/this" carries an ambiguous referent.

## Check 4 — Sentence structure and readability: PASS

Word-per-sentence counts were computed programmatically (Python `re` sentence split on
`.!?` boundaries over the Markdown prose; headings, the fixed profile-label line, and
the bullet list in "Scope limitations" are assessed separately per the profile).

- **64 prose sentences.**
- **Distribution:** min 5, max 20, mean 10.8, median 11.0 words.
- **Buckets:** 1–8 words: 13 sentences; 9–12: 31; 13–16: 16; 17–20: 4; **over 20: 0**.
- **Exceptions kept for accuracy: none** — no sentence needed to exceed 20 words, so no
  exception is reported. The longest sentences (20 words: "It lets a group of devices
  run attention on one shared sequence that is too long for any single device.") sit
  exactly at the target.
- Parser note: the lead-in fragment "It omits:" before the "Scope limitations" bullet
  list is a colon lead-in to a list, not a prose sentence; the list items below it are
  assessed as list items per the profile and each stays under 20 words as well.
- One idea per sentence: verified by reading; each sentence carries a single mechanism
  step or a single definition.
- Tense: present tense throughout for mechanisms (the explanation describes no
  historical events, so no past-tense rule is exercised); the em-dash negation
  sentence keeps its contrast structure rather than being split.

## Result

All four ordered checks pass with no exceptions; the C1 content guard (no unsupported
numerical or performance claims; clear scope and prerequisites) is met.
