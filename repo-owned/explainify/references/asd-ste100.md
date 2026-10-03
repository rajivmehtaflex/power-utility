# STE-inspired simplified English — writing profile for `asd-ste100`

This is the writing profile for the `asd-ste100` format. It is an original,
approximate profile **inspired by** ASD-STE100 Simplified Technical English. It is
not the standard. Texts produced with it are not validated for ASD-STE100
conformity. Never claim that a delivered text complies with, is certified for, or
was approved under ASD-STE100. This reference is an original digest of style ideas;
it is not a redistribution of the standard.

The standard itself is [ASD-STE100, Issue 9 (official PDF)](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf).
Consult the official specification for the actual rules. Nothing in this file
reproduces or replaces them.

Meaning outranks style. Preserve factual meaning, uncertainty, negation, dates,
conditions, and attribution ahead of every rule below.

## Profile rules

- One main idea per sentence.
- Use active voice where it stays accurate. Use passive voice only when naming an
  actor would invent information the source does not contain.
- Keep terminology consistent. Make every referent explicit: state what "it",
  "this", or "these" denotes, or repeat the noun.
- Keep paragraphs short. Each paragraph carries one group of related sentences.
- Do not use unexplained idioms. Remove the idiom, or explain it where it appears.
- Aim for at most 20 words in each prose sentence. Assess lists, equations, code,
  and quotations separately; the target does not apply to them.
- If splitting a sentence would distort its meaning, keep the longer sentence and
  report it as an exception during verification.

## Tense and modality

- Use the present tense for general mechanisms: "the valve opens when the pressure
  rises".
- Keep the past tense for historical events: "the specification was first issued
  decades ago".
- Keep conditional and uncertain wording exactly as each claim requires.
- Never replace "may" with "does".
- Never remove a negation, a date, or a condition to satisfy a style rule.

## Terms

- Define each domain term before its first use.
- Use each defined term consistently after that point.
- Do not alternate synonyms for the same concept. Choose one term and keep it.

## What full STE conformity would additionally require

Official ASD-STE100 conformity applies the specification's approved vocabulary and
word lists, its rules that restrict words to approved meanings and parts of speech,
its terminology rules, and its full checking procedures. This profile does none of
that work; it is outside v0.1 of this skill. The 20-word sentence target is this
project's own profile choice. It is not an official STE rule, and meeting it does
not imply any conformity.

## Delivered document structure

The delivered Markdown file contains, in order:

1. The profile label, exactly: **STE-inspired simplified English — approximate, not validated for ASD-STE100 conformity**
2. The explanation itself, written to this profile.
3. Source attribution where applicable, cited close to the claims it supports.
4. Material scope limitations: what was simplified, what was omitted, and any
   source-coverage limits.

Do not include an internal checklist, a rules dump, or verification scaffolding in
the deliverable. Report verification outcomes in the final response to the user
instead, and save the brief only when it was explicitly retained.

## Self-check order (agent-facing; not part of the deliverable)

Verify in this order. A later check never overrides an earlier failure:

1. Meaning and qualifications preserved — dates, negation, uncertainty, conditions,
   and attribution survived simplification.
2. Mechanism and example consistency — causal steps remain ordered and correct;
   example arithmetic still checks; illustrative values are still identified as
   illustrative.
3. Terminology consistency — each term is defined before use and used one way.
4. Sentence structure and readability — one idea per sentence, explicit referents,
   and the 20-word target applied wherever meaning allows.

Report material exceptions plainly (for example, "one 24-word sentence was kept
for accuracy") without implying official certification.
