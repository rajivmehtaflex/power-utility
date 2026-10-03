# C7 part B — reserved-format request (`diagram`, alias `2`): modeled response

Run: `explainify-output/long-input-writing-20261003-083800/` (2026-10-03). Case: C7 part
B of §9 evaluation. This file models the skill's reply to a reserved-format request;
no deliverable was produced for the requested format. Simulated user request:

> "Explainify pumped storage as a diagram." (format key `diagram`, alias `2`)

## The modeled response

> **Format: `diagram` is not available in explainify v0.1.** The dispatch table marks
> `diagram` (alias `2`) as reserved: there is no v0.1 output for it, so I will not
> produce a diagram, and I will not quietly write something else in its place.
>
> The two supported formats are:
>
> 1. **`asd-ste100` writing** (aliases `1`, `ste`, `writing`, `ste-inspired`) — a
>    simplified-English explanation as a Markdown file, with source attribution and
>    stated scope limits.
> 2. **`explainer-video`** (aliases `4`, `video`, `3b1b`) — a short silent MP4
>    explainer (60 s limit) plus its reproducibility bundle.
>
> Both accept the same inputs (topic, URL, pasted text, or `.md`/`.txt` file). Tell me
> which one you want — for example "explainify pumped storage as writing" — and I will
> run it. (`html-page`, alias `3`, is likewise reserved in v0.1 and gets this same
> response.)

## Why this is the expected shape

- The request names a format explicitly (`diagram` / `2`), so it is not ambiguous.
  Per the skill's dispatch policy, "No format supplied: default to writing.
  Explicitly requested but ambiguous: ask one focused question… Never silently replace
  an explicitly requested unsupported format." An explicit reserved request therefore
  gets the unavailability response — not a clarifying question, and not a default.
- The response names the requested format as unavailable, offers both supported
  formats with their aliases, and does not substitute writing or video on its own:
  no silent substitution (the guarded failure mode for C7 part B).
- The nearest supported alternative is offered (writing), matching the skill's
  "When refusing, offer the nearest supported format" rule, but only as a choice for
  the user to make.
- No file for the requested `diagram` format was created in this run directory; this
  response file is the case's only artifact.
