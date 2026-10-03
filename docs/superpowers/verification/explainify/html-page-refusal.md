# Reserved format `html-page` (alias `3`) — refusal evidence

- **Case:** C7 (reserved format request), second half — a separate explicit request for the
  `html-page` format, frozen in `cases.md` before implementation.
- **Status:** modeled response, same evidentiary standing as `reserved-format-response.md`
  (the reserved-format path is documentation-driven; no client runtime invocation was
  executed — client-side discovery is recorded UNTESTED in `results.md` §6).

## The request

```text
Explainify https://example.org/some-article as an HTML page.
```

## The response the skill produces

`html-page` (alias `3`) is **reserved** in v0.1 and not implemented. The dispatch table in
`SKILL.md` marks it unavailable, and the skill replies along these lines:

> `html-page` is not available in this version of explainify. The formats I can produce
> right now are:
> - `asd-ste100` (aliases `1`, `ste`, `writing`, `ste-inspired`) — STE-inspired simplified
>   English as a Markdown file, explicitly approximate.
> - `explainer-video` (aliases `4`, `video`, `3b1b`) — a short silent locally rendered
>   MP4 with a reproducibility bundle.
>
> Tell me which of these you want — or leave the format open and I will default to writing.

## Guards this evidence pins down

1. **No silent substitution.** An explicit `html-page` request never produces a writing or
   video artifact instead; the reply names the requested format as unavailable.
2. **No partial implementation.** No HTML file is created in the run directory; the
   run directory contains only the refusal record (for C7's `diagram` half, the verified
   artifact is `reserved-format-response.md`).
3. **Supported formats offered.** Both live formats, with their aliases, are named so the
   user can re-request immediately.
4. **Per SKILL.md's ambiguity policy,** only an *ambiguous* format request earns one
   clarifying question; an explicitly reserved request gets the unavailability response
   directly, which is what is modeled here.
