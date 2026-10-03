# Discovery evaluation — design-level (positive and negative)

**This is a design-level evaluation against the skill's description and dispatch
policy. It is NOT a client runtime test.** Whether any specific client actually lists
and invokes the skill on these phrases (client discovery) was not tested here; client
runtime discovery is recorded as UNTESTED in the suite's results records. What this
file evaluates: whether the skill's `description` frontmatter would, by its wording,
trigger on the right phrases, refuse the wrong ones, and avoid over-broad triggers.

Evaluated text — the installed skill's description
(`repo-owned/explainify/SKILL.md`, quoted exactly):

> "Use when the user invokes explainify, asks for STE-style simplified English or a
> locally rendered silent explainer video, or requests either format for a topic, URL,
> pasted text, or markdown file. Produces an accurate explanation with source
> attribution, teaching checks, and format-specific verification."

## A. Positive — phrases that should trigger the skill

| # | Invocation phrase | Description clause it matches | Cross-check |
|---|---|---|---|
| 1 | "explainify X" / "Explainify: ring attention." | "the user invokes explainify" — verbatim trigger on the skill name | the skill's own worked invocation opens with "explainify this as simplified writing: …"; C1's frozen input is `Explainify: ring attention.` |
| 2 | "explain X in simplified English" / "explain X in STE English" / "explainify X as writing" | "asks for STE-style simplified English" — the style request is the trigger, with or without the skill name | "simplified English" maps onto "STE-style simplified English"; "STE English" is also covered by the format's aliases (`ste`, `ste-inspired`) in the Step 3 dispatch table |
| 3 | "make an explainer video of X" / "explainify X as a video" | "a locally rendered silent explainer video" — near-verbatim overlap on "explainer video" | the video worked invocation is "explainify why the moon has phases, as a video"; aliases `4`, `video`, `3b1b` |

Positive workflow executions exist for every trigger family: the C1–C4 runs in this
evaluation suite (C1 topic, C2 URL, C3 `.md` file, C4 pasted text — each executed in
writing and/or video form; the C4-writing and C5 runs of this cluster are additional
writing executions) demonstrate that once triggered, the workflow runs end-to-end.
Those runs evidence the *workflow*, not client discovery, which remains untested.

## B. Negative — phrases that must not trigger (or must not misfire)

1. **Ordinary factual question: "what is the capital of France?"** Reasoning against
   the description: the question does not invoke explainify by name; it does not ask
   for STE-style or simplified English (no writing style is requested — it wants a
   fact, not a formatted explanation); it does not request an explainer video; and it
   does not request "either format for a topic, URL, pasted text, or markdown file"
   (no format and no explainify input is in play — it is a single-question answer).
   None of the description's four trigger clauses matches, so the skill should stay
   unlisted/uninvoked and the client answers directly. Answering factual questions is
   not the skill's job, and nothing in the description reaches for it.

2. **Diagram-only request.** Two readings, both safe:
   - "Draw me a diagram of X" (no explainify invocation): the description never
     mentions diagrams — diagrams appear only in the skill body's dispatch table as a
     *reserved* format and in "Out of scope" ("diagrams and HTML pages (reserved
     formats)"). No description clause matches, so the skill does not trigger, and
     ordinary diagramming happens outside it.
   - "Explainify X as a diagram" (skill invoked, format word present): the invocation
     triggers the skill, and the Step 3 dispatch row for `diagram` (alias `2`) is
     "Reserved: explain that it is unavailable and offer supported formats". The
     correct outcome is the unavailability response naming both supported formats
     (`asd-ste100` writing, `explainer-video`) — never a silent substitution of
     writing or video. This exact behavior is modeled concretely by
     `reserved-format-response.md` (C7 part B). An explicitly requested reserved
     format gets the unavailability response, not a clarifying question and not a
     default to writing.

3. **No over-broad "every explanation" trigger.** The description's trigger set is
   enumerated and closed: (i) "the user invokes explainify", (ii) "asks for STE-style
   simplified English", (iii) "or a locally rendered silent explainer video", (iv)
   "or requests either format for a topic, URL, pasted text, or markdown file". There
   is no clause like "every explanation request", "whenever the user asks why", or
   "any technical content" — the widest clause (iv) is still bounded to *either
   format* (the two v0.1 formats) applied to the four listed input kinds. A plain
   "explain X" with no style, format, or skill name matches no clause and should not
   trigger. Confirmed by direct inspection of the quoted description: the string
   "explain" appears only inside "explainer video" and the trailing sentence about
   what the skill "Produces", which describes output, not triggering.

## C. Verdict (design-level)

- Positive: three trigger families map cleanly onto the description's wording, and
  all have corresponding successful workflow executions in this suite (C1–C4, plus
  the C4-writing/C5 writing runs).
- Negative: an ordinary factual question matches no clause; a diagram-only request
  either does not trigger (no invocation) or lands on the reserved-format
  unavailability path (invoked) with no silent substitution; no over-broad trigger
  exists in the description.
- No claim is made here about actual client discovery, listing, or invocation — that
  capability dimension is UNTESTED and recorded elsewhere.
