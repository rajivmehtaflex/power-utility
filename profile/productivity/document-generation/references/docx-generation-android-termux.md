# DOCX Generation and Verification Notes

## Scope alignment

When a document request starts from a multi-architecture session, identify the user’s final architecture before drafting. Do not carry abandoned server/Python/API sections into an Android + Termux guide. If the user explicitly chose a narrow runtime project, keep the deliverable narrow and preserve unrelated prior artifacts rather than silently overwriting them.

For Android + Termux + Hermes documentation, the primary boundary is:

```text
Android app → Termux RUN_COMMAND Intent → Hermes CLI → model/provider
                                      ← PendingIntent result
```

Python, FastAPI, HTTP listeners, Debian services, Docker, and Android Studio are not part of that architecture unless the user explicitly changes direction.

## Source freshness

A changed model/provider does not itself make factual claims current. Verify version-sensitive claims against live primary sources and record the observed tool version. For Hermes, run:

```bash
hermes --version
hermes --help
hermes chat --help
hermes sessions list --help
```

Important CLI distinction observed during the Android + Termux guide task: Hermes v0.19.0 exposes `-z/--oneshot` as a global option, while `hermes chat` exposes `-q/--query` and `-Q/--quiet`. Do not repeat `hermes chat -q -z ...` without checking the target release. The same verification applies to undocumented flags such as `hermes sessions list --format json`.

## Reproducible DOCX workflow

1. Preserve existing DOCX/PDF outputs with SHA-256 hashes before regeneration.
2. Generate a versioned output instead of overwriting the previous deliverable.
3. Keep the generator and npm dependencies in a temporary build directory when the user wants a clean runtime project.
4. Use `docx-js` with built-in Heading 1–3 styles, true lists, explicit table widths, shaded callouts, monospaced code blocks, headers/footers, and source hyperlinks.
5. Use `pageBreakBefore: true` on top-level headings for chapter separation. A standalone `PageBreak` paragraph may render as an empty square glyph in macOS Quick Look; if that occurs, replace it with the heading property.
6. Include a source ledger for version-sensitive commands, platform requirements, benchmarks, and compatibility claims.
7. Make the article explicitly distinguish verified production code from illustrative snippets. Audit code against current primary APIs before presenting it as canonical.

## Validation gates

Run all of these before delivery:

```bash
unzip -t output.docx
pandoc -t gfm output.docx -o /tmp/output.md
```

Validate the main OOXML parts with `xmllint` when available. Count paragraphs, headings, tables, and required-topic matches from `word/document.xml`. Search extracted text for accidental abandoned-architecture content.

Text extraction is not enough. Render the DOCX visually. Prefer LibreOffice conversion plus `pdftoppm` for page-by-page inspection. On macOS when LibreOffice is unavailable, use `qlmanage -t` as a fallback preview and inspect the generated PNG with vision. Check for clipped tables/code, malformed characters, orphan headings, blank pages, broken page breaks, and unreadable code.

## Delivery reporting

Report:

- exact output path and native attachment link
- file size and structural counts
- source/CLI version used
- validation commands and results
- visual inspection result and fallback renderer used
- original-file preservation hashes
- temporary build cleanup status
- any known limitation, especially when an exact page count was not available from the installed renderer
