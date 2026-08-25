---
name: document-generation
description: Generate and verify professionally formatted PDF, DOCX, and Excel documents from markdown, structured data, or code.
license: MIT
metadata:
  hermes_related_skills: docx, powerpoint, ocr-and-documents, nano-pdf
  hermes_tags: pdf, docx, docx-js, word, excel, xlsx, reportlab, openpyxl, documents, reports, export
  version: 1.0.0
---

# Document Generation

Generate professionally formatted PDF and Excel documents from markdown, structured data, or code.

## When to use

Use this skill when the user asks to create, generate, or export:
- PDF reports from markdown or structured content (financial reports, audit reports, executive summaries)
- Styled Excel workbooks with formatting, colors, auto-filters, multiple sheets
- Any "give me this as PDF" or "export to Excel" request where you build the document programmatically

**Not this skill:** Reading/extracting text FROM PDFs (use `ocr-and-documents`), editing existing PDFs (use `nano-pdf`), creating slide decks (use `powerpoint`).

## Quick Reference

| Task | Tool | Guide |
|------|------|-------|
| Markdown → PDF | reportlab | [references/pdf-from-markdown.md](references/pdf-from-markdown.md) |
| Data → Styled Excel | openpyxl | [references/excel-styling.md](references/excel-styling.md) |
| QA: verify visual output | pdftoppm + vision | [references/qa-visual-verification.md](references/qa-visual-verification.md) |

---

## PDF Generation (reportlab)

**Approach:** Parse the markdown into structural elements (headings, paragraphs, tables, lists, blockquotes, notes), convert each to a reportlab flowable, and build with `SimpleDocTemplate`.

When rendering an existing markdown report, treat the markdown as the source of truth: preserve its wording, figures, dates, section order, and disclaimers. Styling may improve legibility, but do not silently correct, summarize, or substantively rewrite report content unless the user explicitly asks for editorial review. If the source contains claims that appear unsupported, flag them separately rather than changing the PDF content.

**Key design decisions for professional financial/business reports:**
- Dark navy (`#1e293b`) table headers with white text
- Alternating row backgrounds (`#f8fafc` for even rows)
- Total/summary rows highlighted in indigo (`#e0e7ff`)
- Indigo accent (`#4f46e5`) for horizontal rules and left-border callouts
- Page footer: "Page N" left, "Document Title — Confidential" right (skip on page 1)
- Justified body text, 10.5pt Helvetica
- Green-bordered italic block for Slack/chat message drafts

**Full implementation pattern and code:** See [references/pdf-from-markdown.md](references/pdf-from-markdown.md)

**Session notes:** See [references/pdf-from-markdown-session-notes.md](references/pdf-from-markdown-session-notes.md) for the Hermes/macOS `PYTHONPATH=""` workaround, `reportlab` + `pdftoppm` verification loop, and ASCII-diagram rendering fix. For artifact/software inventory reports after generation, see [references/session-artifact-inventory.md](references/session-artifact-inventory.md).

---

## Excel Generation (openpyxl)

**Approach:** Build workbooks with named styles, color-coded categories, merged section headers, auto-filters, and frozen panes.

### Updating an existing workbook

When the user asks to add information to a workbook already created or attached:

1. Load the existing file first and inspect sheet names, dimensions, headers, and existing filters/freeze panes.
2. Modify only the requested sheet; preserve all other sheets and their contents.
3. Add new columns after the existing used range unless the user explicitly requests a different location.
4. Extend `auto_filter.ref`, column widths, and row heights to include the new column.
5. Preserve existing styles and use a distinct, semantically meaningful fill for new status/file columns.
6. Read the workbook back after saving and verify the target header, row count, values, and sheet list.

For prompt-to-attachment matrices, map each prompt to the smallest sufficient file pack. Distinguish among: files to upload, application data sources that need no upload, follow-up prompts that rely on prior conversation context, and blocked prompts whose source document is missing. Never infer that an ambiguously named ledger or agreement is the required source without flagging the uncertainty.

**Key patterns:**
- Header row: bold white text on dark fill (`#4F46E5` indigo or `#1e293b` navy)
- Section separator rows: merged, light fill (`#E2E8F0`), bold
- Color-code data rows by category (amber for warnings, blue for data, red for blocked, green for success)
- `freeze_panes = "A2"` to keep headers visible
- `auto_filter.ref` for filterable columns
- Set column widths explicitly (don't rely on defaults)
- Row heights based on content length

**Full implementation pattern and code:** See [references/excel-styling.md](references/excel-styling.md)

---

## DOCX Generation and Cross-Architecture Scope

Use this section whenever the user asks for a Word document generated from a technical session, especially when the session contains multiple abandoned architecture paths.

### Scope alignment

Confirm the user’s final architecture before drafting. Do not carry abandoned server/Python/API sections into a focused Android + Termux guide. If the user explicitly chose a narrow runtime project, preserve unrelated prior artifacts and generate a versioned document instead of silently overwriting the old one.

For Android + Termux + Hermes documentation, keep the boundary explicit:

```text
Android app → Termux RUN_COMMAND Intent → Hermes CLI → model/provider
                                      ← PendingIntent result
```

Python, FastAPI, HTTP listeners, Debian services, Docker, and Android Studio are out of scope unless the user explicitly changes direction.

### Source freshness and CLI verification

A changed model/provider does not itself make factual claims current. Verify version-sensitive claims against live primary sources and record the observed tool version:

```bash
hermes --version
hermes --help
hermes chat --help
hermes sessions list --help
```

Do not repeat command forms from an earlier session without checking the installed release. For example, Hermes v0.19.0 exposes `-z/--oneshot` as a global option, while `hermes chat` exposes `-q/--query` and `-Q/--quiet`; undocumented forms such as `hermes sessions list --format json` must not be presented as supported.

### Reproducible DOCX workflow

1. Hash existing DOCX/PDF files before regeneration.
2. Generate a versioned output rather than overwriting the previous deliverable.
3. Keep the generator and npm dependencies in a temporary build directory when the user wants a clean runtime project.
4. Use built-in Heading 1–3 styles, true lists, explicit table widths, shaded callouts, monospaced code blocks, headers/footers, and source hyperlinks.
5. Use `pageBreakBefore: true` on top-level headings for chapter separation. A standalone `PageBreak` paragraph can render as an empty square glyph in macOS Quick Look; replace it with the heading property if that occurs.
6. Include a source ledger for version-sensitive commands, platform requirements, benchmarks, and compatibility claims.
7. Distinguish verified production code from illustrative snippets. Audit code against current primary APIs before presenting it as canonical.

For the detailed Android + Termux notes, see `references/docx-generation-android-termux.md`.

## QA: Visual Verification

**Always verify generated documents visually.** Text extraction alone misses layout problems.

### PDF verification
```bash
# Convert all pages to PNG at 150 DPI
pdftoppm -png -r 150 output.pdf /tmp/page

# Inspect each page with vision_analyze
```

Use this vision prompt pattern:
```
Review this page from a [document type]. Check:
1) Are tables rendering correctly with borders and colors?
2) Is text properly formatted and aligned?
3) Any layout issues, overflow, or missing content?
```

### Excel verification
Open the file and verify sheet structure, or use openpyxl to read back cell values and styles.

**Full QA workflow:** See [references/qa-visual-verification.md](references/qa-visual-verification.md)

---

## Dependencies

| Tool | Install | Notes |
|------|---------|-------|
| reportlab | `pip install reportlab` | PDF generation. May be in system Python but not project venv — check `/opt/homebrew/bin/python3` on macOS |
| openpyxl | `pip install openpyxl` | Excel generation |
| pdftoppm | `brew install poppler` (macOS) | PDF → PNG conversion for QA |
| sips | Built-in (macOS) | Only converts FIRST page of PDF — use pdftoppm for multi-page |

## Pitfalls

- **sips limitation:** macOS `sips` only renders the first page of a PDF. For multi-page QA, use `pdftoppm` from poppler instead.
- **Python environment mismatch:** reportlab/openpyxl may be installed in the system Python (`/opt/homebrew/bin/python3` or `/usr/bin/python3`) but not in the project venv. Check availability before writing generation scripts — don't assume the project venv has everything.
- **Hermes PYTHONPATH leakage:** if Homebrew/system Python unexpectedly imports Hermes' bundled Pillow or other packages, clear the inherited path (`PYTHONPATH="" /opt/homebrew/bin/python3 ...`) before generating the PDF.
- **ASCII diagrams in PDF:** Unicode box-drawing characters may render as squares in some PDF flows. Use plain ASCII (`|`, `+--`, `-->`, `v`, `^`) for diagrams that must survive PDF export.
- **reportlab table widths:** Always set `colWidths` explicitly. Without it, tables can overflow the page margin. Calculate as `available_width / num_columns`.
- **Table total rows:** Detect "Total" rows by checking if any cell contains "total" (case-insensitive) and style them differently — this is the standard financial report convention.
- **Page breaks:** reportlab's `SimpleDocTemplate` handles page breaks automatically, but large tables may split awkwardly. Use `repeatRows=1` on Table to repeat headers across page breaks.
