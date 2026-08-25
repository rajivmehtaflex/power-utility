# Visual Verification of Generated Documents

## Core Principle

**Always verify generated documents visually.** Text extraction alone misses layout problems — overflowing tables, misaligned columns, cut-off text, wrong colors, missing pages.

## PDF Verification

### Convert PDF pages to PNG

```bash
# Install poppler if needed (macOS)
brew install poppler

# Convert ALL pages to PNG at 150 DPI
pdftoppm -png -r 150 output.pdf /tmp/page

# Convert specific page
pdftoppm -png -r 150 -f 3 -l 3 output.pdf /tmp/page3
```

This creates `/tmp/page-1.png`, `/tmp/page-2.png`, etc.

### Inspect with vision_analyze

Call `vision_analyze` on each page with a targeted question:

```
Review this page from a financial audit report. Check:
1) Are tables rendering correctly with borders and colors?
2) Is text properly formatted and aligned?
3) Any layout issues, overflow, or missing content?
```

**Check every page.** A report that looks perfect on page 1 may have table overflow on page 3.

### Common PDF rendering issues to look for

| Issue | Symptom | Fix |
|-------|---------|-----|
| Table overflow | Table extends past right margin | Set explicit `colWidths` based on available width |
| Text cut off | Paragraph truncated at cell boundary | Use Paragraph objects in cells, not raw strings |
| Header not repeating | Page 2+ tables lose header row | Use `repeatRows=1` in Table constructor |
| Wrong page count | Missing content | Check that all flowables were added to story |
| Footer on page 1 | Footer appears on title page | Gate footer on `page_num > 1` |
| Blurry/pixelated | Low quality on screen | Increase DPI: `pdftoppm -r 150` minimum |

### sips limitation (macOS)

```bash
# This ONLY converts the FIRST page:
sips -s format png report.pdf --out preview.png

# For multi-page, use pdftoppm instead:
pdftoppm -png -r 150 report.pdf /tmp/page
```

## Excel Verification

### Read back cell values and styles

```python
wb = openpyxl.load_workbook(path)
ws = wb["Sheet Name"]
print(f"Dimensions: {ws.dimensions}")
print(f"Max row: {ws.max_row}, Max col: {ws.max_column}")

# Check headers
for col in range(1, ws.max_column + 1):
    print(ws.cell(row=1, column=col).value)

# Spot-check data rows
for row in [2, 5, 10, ws.max_row]:
    print(f"Row {row}: {[ws.cell(row=row, column=c).value[:40] for c in range(1, ws.max_column+1)]}")
```

### Verify structure

```python
print(f"Sheets: {wb.sheetnames}")
print(f"Freeze panes: {ws.freeze_panes}")
print(f"Auto-filter: {ws.auto_filter.ref}")
```

## Verification Checklist

For every generated document:

- [ ] File exists and is non-empty (check file size > 0)
- [ ] Page count matches expected content volume
- [ ] Every page rendered to PNG and visually inspected
- [ ] Tables have correct borders, headers, row colors
- [ ] No text overflow or truncation
- [ ] Footer/header placement correct
- [ ] All sections present (compare against source markdown/requirements)
