# Session artifact inventory & verification

Use this reference when a document-generation session ends with the user asking what was created or what software was involved.

## Reporting pattern

Return two compact tables:

1. **Artifacts** — columns: `Artifact`, `Type`, `Location`, `Status`, `Notes`
2. **Software / tooling** — columns: `Software`, `Used?`, `Evidence`, `Notes`

## Verification rule

Do not rely on an earlier tool result alone. Before reporting the final inventory, re-check the on-disk state and other evidence:

- `stat` or a file-existence check for each deliverable
- `pdfinfo` for final PDF page count and metadata
- `pdftoppm` for page rendering when visual QA matters
- a runtime check for library versions when relevant (for example, `python3 - <<'PY' ...`)

If a file was created earlier but is no longer present when you verify, report that honestly as a current-state check rather than assuming it still exists.

## PDF QA

For generated PDFs, inspect at least:

- first page
- one middle page
- final page

Use rendered PNGs plus vision inspection to catch layout issues, clipping, and broken diagrams.

## Good phrasing

- "Generated during the session, but not present on disk now"
- "Verified present with size and path"
- "Used for QA only"
- "No new software was installed during this session"
