# PDF generation notes from Hermes session

## What worked

- `reportlab` was available in Homebrew Python (`/opt/homebrew/bin/python3`).
- Hermes' environment leaked its own Python path into the Homebrew interpreter, which caused Pillow/reportlab import errors.
- Clearing the inherited `PYTHONPATH` fixed the issue:

```bash
PYTHONPATH="" /opt/homebrew/bin/python3 generate.py
```

- `pandoc` was installed, but the reliable path for this session was direct `reportlab` generation.
- `pdftoppm -png -r 150` was available and worked well for page-by-page visual QA.
- Unicode box-drawing characters in ASCII diagrams rendered as squares in the PDF; plain ASCII (`|`, `+--`, `-->`, `v`, `^`) rendered reliably.

## Verification pattern

1. Generate the PDF.
2. Render pages to PNG with `pdftoppm`.
3. Inspect the title page, a middle page with code/table content, and the last page.
4. Fix any glyph or overflow issues before delivering.

## Practical recommendation

When generating PDFs from markdown in a Hermes session, prefer:

- `reportlab` for direct PDF output
- `PYTHONPATH=""` when using Homebrew Python on macOS
- plain ASCII diagrams instead of Unicode box art
- visual QA via `pdftoppm` + image inspection
