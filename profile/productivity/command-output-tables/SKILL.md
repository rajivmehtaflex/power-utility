---
name: command-output-tables
description: Render command output (e.g. ls -alr) as a lossless table.
metadata:
  author: Hermes Agent
  version: 1.0.0
---

# Command Output → Lossless Table

## When to use
- User says "render response here", "convert to tabular format", "without losing
  format", or otherwise wants command output (typically `ls -alr`) shown as a table.
- Applies to any single-level `ls -alr` listing (the `-r` flag reverses order;
  directory entries are the dir itself, not expanded — output stays one level deep).

## Technique
1. **Capture to a temp file FIRST.** The terminal has a ~50KB stdout cap; directory
   listings can exceed it and get silently truncated. Always do:
   ```
   ls -alr /path > /tmp/ls_out.txt 2>&1
   wc -c /tmp/ls_out.txt      # confirm size; note truncation risk if large
   ```
   Then `read_file` (never `cat`) the temp file so you render the FULL content.
2. **Render verbatim FIRST** in a fenced block — this satisfies "without losing
   format". Nothing omitted, nothing reformatted.
3. **Then render the table.** Parse each line into columns:
   `Permissions | Links | Owner | Group | Size | Modified | Name`.
   - Drop the leading `total N` line from the table (it is not a file record) but
     mention it in prose.
   - Include `.` and `..` rows so nothing is lost.
   - Preserve original ordering (e.g. `-r` = newest-first).
   - The `@` suffix on permissions marks macOS extended attributes; absence means none.

## Pitfall — target redirection
If the user says **"i'm talking about -> `<explicit path or command>`"**, they are
correcting your TARGET. Re-run the command on THAT exact path (or glob). Do NOT
re-present the previously discussed directory. Session example: the user first
received `ls -alr` on the workspace root, then redirected twice to
`.../pi-local-dev` and `.../pi-local-dev/*.md` — each required re-running on the
new path, not re-showing root output.

## Example
`ls -alr /Users/rajivmehtapy/Documents/Dev/pi-local-dev/*.md` → verbatim:
```
-rw-r--r--@ 1 rajivmehtapy  staff    0 16 Aug 10:43 README.md
-rw-r--r--@ 1 rajivmehtapy  staff  136 16 Aug 10:31 IDEA.md
```
plus a table with columns Permissions / Links / Owner / Group / Size / Modified / Name
(2 rows: README.md size 0, IDEA.md size 136).
