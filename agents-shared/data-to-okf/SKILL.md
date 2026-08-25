---
name: data-to-okf
description: Converts any local folder of mixed documents (docx, pdf, xlsx, duckdb, csv, images, text) into a Google Open Knowledge Format (OKF) v0.2 knowledge bundle of markdown concept files with point-in-place file:// resource links, so AI agents can navigate it deterministically instead of grepping raw files. Use this whenever the user wants to "bundle", "index", or make a folder "AI-readable"/"agent-consumable", wants to build a knowledge base from a messy folder of client docs/meeting notes/exports, or explicitly mentions OKF, knowledge bundling, or Hermes-consumable folders.
license: Apache-2.0
compatibility: Requires Python 3.9+ with python-docx, openpyxl, pyyaml, and pypdf installed; the duckdb CLI on PATH for .duckdb schema introspection (only needed if the source folder contains a .duckdb file).
metadata:
  author: rajivmehtapy
  version: 1.0
---

# data-to-okf

Turns a messy folder of real files — contracts, meeting transcripts, financial
exports, a database, screenshots — into a bundle of thin markdown "concept"
files an AI agent can traverse deterministically (read an index, follow a
link, read a concept) instead of grepping raw binaries every time. The bundle
never copies the source files: every concept just points back at the real
file via a `resource: file://...` URI, so the source stays the single source
of truth.

## When to use

Reach for this any time someone wants a folder made agent-friendly, wants a
"knowledge base" or "knowledge bundle" built from an existing pile of
documents, or mentions OKF / Open Knowledge Format / Hermes-consumable data
directly. It's most valuable on folders that mix file types (some PDFs, some
spreadsheets, a database file, some plain text) where an agent would
otherwise need bespoke handling for each.

## What OKF v0.2 requires (the parts that matter here)

Full spec:
https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

- A **concept** is one markdown file with a YAML frontmatter block. The only
  mandatory field is a non-empty `type` — it's a free descriptive string
  (`Document`, `Database`, `Spreadsheet`, ...), not a fixed enum.
- **Binaries are never embedded or copied.** A concept's frontmatter carries a
  `resource:` field with a `file://` URI pointing at the real file; the
  markdown body is a short extracted summary, generated once at ingestion
  time.
- `index.md` and `log.md` are **reserved filenames**: plain markdown, no
  frontmatter, except the bundle-root `index.md` which may carry
  `okf_version: "0.2"`. `index.md` is a listing of a directory's children;
  `log.md` is a flat, date-grouped changelog (`## YYYY-MM-DD` headings).
- Links between concepts are ordinary markdown links, either bundle-relative
  (`/bucket/concept.md`) or relative.

Because binaries can never go into the bundle directly, every source type
needs a small extraction step to produce that markdown summary. The bundled
script below already implements this — don't reimplement extraction from
scratch.

## Binary handling reference

| Source type | How it's turned into a concept body |
|---|---|
| `.docx` | `python-docx` — extract paragraph text, first ~1200 chars as an excerpt |
| `.pdf` | `pypdf` — extract text from the first 2 pages, note total page count |
| `.xlsx` | `openpyxl` (read-only) — sheet names + header row of each sheet, not full data |
| `.duckdb` | Live `duckdb` CLI introspection via `information_schema.tables` across **all** schemas (not just `SHOW TABLES`, which only covers the default `main` schema) + `DESCRIBE` per table — always a fresh schema, never a stale hand-copied one |
| `.csv` | One concept per folder of CSVs — column headers + row counts per file, not a full data dump |
| images (`.png`/`.jpg`/`.webp`/`.svg`) | No OCR — a filename-only stub, since OCR is overkill for typical screenshots/diagrams |
| video (`.mp4`/`.mov`/`.avi`) | **Excluded entirely** — large, low signal-to-noise for a text bundle |
| everything else already text (`.md`/`.yaml`/`.txt`/`.html`/`.json`/`.log`) | Direct read, truncated excerpt |

Bucketing is generic: each concept lands in a bucket named after the
**source folder's own top-level subfolder** (e.g. files under
`ClientY/meetings/...` land in a `meetings/` bucket in the bundle
automatically) — there's no fixed domain taxonomy to configure. Loose files
sitting at the source root land in a `misc` bucket.

Default exclusions (no need to ask the user about these unless they mention
something unusual): `.DS_Store`, `.git`/`__pycache__`/`node_modules`
directories, any filename containing "secret", "credential", or "password",
and video files. Pass `--exclude "pattern1,pattern2"` to the generator script
for one-off additional exclusions (e.g. a restricted-access subfolder) —
only do this if the user calls out something specific to skip.

## Workflow

1. **Get the two required inputs** — ask the user (if not already given in
   their request):
   - the **source folder** to bundle (an absolute path)
   - the **destination bundle folder** name/path (suggest `<source-name>-okf`
     as a sensible default, placed wherever the user is working — e.g. the
     current repo root)
2. **Ensure dependencies are available.** The generator needs
   `python-docx`, `openpyxl`, `pyyaml`, `pypdf` and the `duckdb` CLI. If
   they're not already importable, create a throwaway venv in the *target
   project* (not inside this skill folder) and install them there:
   ```bash
   python3 -m venv .okf-venv && source .okf-venv/bin/activate
   pip install --quiet python-docx openpyxl pyyaml pypdf
   ```
3. **Generate the bundle** — invoke the scripts by a path relative to this
   skill's own directory (find that directory first: it's wherever this
   `SKILL.md` file lives), not a hardcoded absolute path, since this skill
   may be installed at a different location depending on the agent client:
   ```bash
   python3 <skill-dir>/scripts/generate_okf_bundle.py \
     --source "<source folder>" \
     --dest "<destination bundle folder>"
   ```
   This is a full regenerate each run (it removes and rebuilds the
   destination folder), so it's naturally idempotent and safe to re-run.
4. **Validate conformance** — don't skip this, it catches malformed
   frontmatter or broken resource links before you hand the bundle back:
   ```bash
   python3 <skill-dir>/scripts/validate_okf_bundle.py "<destination bundle folder>"
   ```
   Fix any reported errors and re-run before declaring the bundle done.
5. **Report back**: concept count vs. source file count scanned (so nothing
   looks silently dropped beyond the documented exclusions), which buckets
   were created, and explicitly call out anything excluded (secrets, videos,
   any `--exclude` patterns used).
6. **Flag the point-in-place caveat**: every `resource:` URI only resolves on
   the machine where the source folder actually lives. If the user plans to
   consume the bundle from a different machine (e.g. a phone, a different
   dev box), say so plainly — the bundle itself is portable, the underlying
   files are not, unless they're synced too.

## Updating a bundle after the source changes

Re-run step 3 with the same `--source`/`--dest` — the generator does a full
re-walk of the source folder each time, so new, changed, or removed files
are picked up automatically, including a fresh `duckdb` schema introspection
if a database file is present. Then re-run step 4 (validation).

The generator does **not** auto-append to `log.md` beyond the initial
ingestion entry — `log.md` is meant to be a human-readable changelog, not
machine output, so after a refresh, add a `## <date>` entry yourself
summarizing what changed (e.g. "Re-ingested after Q3 exports added; +14
concepts").
