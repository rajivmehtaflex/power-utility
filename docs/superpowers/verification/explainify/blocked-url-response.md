# C6 — response for the blocked URL (models the skill's in-chat reply)

Run: `explainify-output/blocked-url-20261003-083400/` (2026-10-03). Case: C6 of §9
evaluation — blocked URL, source workflow. This file models the reply the skill gives
the user; it is not an explanation deliverable. **No explanation file was produced for
this case.**

## Observed retrieval attempt (2026-10-03)

```text
$ curl -sS -L --max-time 8 -o /dev/null -w 'HTTP status: %{http_code}\n' \
    'https://explainify-blocked-fixture.invalid/notes'
curl: (6) Could not resolve host: explainify-blocked-fixture.invalid
HTTP status: 000
curl exit code: 6
```

One genuine retrieval attempt was made and failed at DNS resolution, as designed: the
`.invalid` top-level domain is reserved by RFC 2606 and never resolves, so
"unavailable" is deterministic and repeatable. Because the host itself does not
resolve, the "identifiable original-author copy or reliable alternate" fallback does
not apply — there is no reachable page, mirror, or cache URL to identify.

## The modeled response

> **Source** `https://explainify-blocked-fixture.invalid/notes`
> **Retrieval status: unavailable** — one retrieval attempt was made on 2026-10-03
> (connection failed: the host could not be resolved; `.invalid` never resolves). No
> content was retrieved: no page title, no body text, no partial fragment. Nothing is
> available to summarize, so no explanation was produced for this URL in this turn.
>
> Two paths forward, your choice:
>
> 1. **Paste the content** — paste the page's text (or attach the `.md`/`.txt` file),
>    and I will treat the pasted text as the source with full attribution to it.
> 2. **Explicitly switch to a topic explanation** — say so, and I will build the
>    explanation from model knowledge instead, clearly labeled `origin:
>    model-knowledge`, with this failed URL recorded in the provenance block as the
>    requested location and a scope note stating the switch. It will never be
>    presented as the page's content.
>
> I will not substitute a model-knowledge explanation of the presumed subject on my
> own: that would misrepresent the source.

## Why this is the expected shape

- Status reported explicitly (`retrieval_status: unavailable`, with date); one real
  attempt observed, not skipped; no invented page title or content.
- No silent substitution: no model-knowledge explanation of "notes" or any presumed
  subject was written, in this turn or as a file in this run directory.
- The two documented alternatives come from the skill's URL-unavailable policy (paste
  the content, or explicitly re-request as a topic explanation).
- If the user later approves a topic-mode switch, the resulting output would record
  `kind: topic`, model-knowledge origins, and this URL as the requested location — per
  the frozen C6 expectations; that follow-up is not part of this case's run.
- Run directory contains only this response file; no storyboard, no video, no
  explanation artifact was produced from the unavailable source.
