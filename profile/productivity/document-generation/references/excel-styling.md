# Excel Styling with openpyxl

## Architecture

Build workbooks with named styles, color-coded categories, merged section headers, auto-filters, and frozen panes.

## Python environment

openpyxl may be in the system Python but not the project venv. Check before writing scripts:

```bash
/opt/homebrew/bin/python3 -c "import openpyxl; print('ok')"
```

Write scripts to `/tmp/` and run with whichever Python has openpyxl.

## Design System

### Colors

| Element | Hex | Usage |
|---------|-----|-------|
| Indigo | `4F46E5` | Primary header fill |
| Navy | `1e293b` | Dark header fill |
| Section fill | `E2E8F0` | Merged section header rows |
| Slate border | `CBD5E1` | Cell borders |
| Action fill | `F0F9FF` | Preceding action column |

### Category color coding

| Category | Fill Hex | Example |
|----------|----------|---------|
| Data / upload needed | `FEF3C7` (amber) | Files to attach |
| Blocked / missing | `FEE2E2` (red) | Missing source files |
| No file needed | `F1F5F9` (grey) | Follow-up prompts |
| DB source only | `DBEAFE` (blue) | Uses configured database |
| Success / ready | `D1FAE5` (green) | Ready to execute |
| NDA / Legal | `EDE9FE` (purple) | Legal review |
| VAT / Balance Sheet | `FEF3C7` (amber) | Accounting |
| Rephrasing | `FCE7F3` (pink) | Text editing |

## Patterns

### Header row

```python
header_font = Font(bold=True, color="FFFFFF", size=11)
header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
thin_border = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)

for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
ws.row_dimensions[1].height = 28
```

### Section header rows (merged)

```python
ws.cell(row=row_num, column=1, value=section_title)
ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=num_cols)
for col in range(1, num_cols + 1):
    ws.cell(row=row_num, column=col).fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    ws.cell(row=row_num, column=col).border = thin_border
```

### Data rows with category coloring

```python
cat_colors = {
    "VAT / Balance Sheet": "FEF3C7",
    "NDA / Legal Review": "EDE9FE",
    "Rephrasing": "FCE7F3",
    "Data Export": "D1FAE5",
}
fill_color = cat_colors.get(category)
if fill_color:
    fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
    for col in range(1, num_cols + 1):
        ws.cell(row=row_num, column=col).fill = fill
```

### Freeze panes and auto-filter

```python
ws.freeze_panes = "A2"  # Freeze header row
ws.auto_filter.ref = f"A1:{last_col}{last_row}"  # Enable column filtering
```

### Column widths

Set explicitly — never rely on auto-sizing:

```python
widths = [8, 38, 48, 52, 14]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
```

### Row heights based on content

```python
lines = max(1, len(text) // 80 + 1)
ws.row_dimensions[row_num].height = max(30, min(90, lines * 18))
```

## Adding a column to an existing sheet

```python
wb = openpyxl.load_workbook(xlsx_path)
ws = wb["Sheet Name"]

# Add header
cell = ws.cell(row=1, column=new_col, value="New Column")
cell.font = header_font
cell.fill = header_fill
cell.alignment = Alignment(horizontal="center", vertical="center")
cell.border = thin_border

# Set width
ws.column_dimensions[get_column_letter(new_col)].width = 55

# Write data with conditional fills
for row in range(2, ws.max_row + 1):
    text = file_map.get(row, "")
    cell = ws.cell(row=row, column=new_col, value=text)
    cell.font = Font(size=10)
    cell.alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")
    cell.border = thin_border
    if "MISSING" in text or "⚠️" in text:
        cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    elif text.startswith("None"):
        cell.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    elif "xero.duckdb" in text:
        cell.fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    else:
        cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

# Update auto-filter range
ws.auto_filter.ref = f"A1:{get_column_letter(new_col)}{ws.max_row}"
wb.save(xlsx_path)
```

## Multiple sheets

```python
wb = openpyxl.Workbook()
ws1 = wb.active
ws1.title = "Project Test Prompts"
# ... populate ws1 ...

ws2 = wb.create_sheet("Real Prompts")
# ... populate ws2 ...

wb.save(path)
```

## CSV → Excel with filtering and cleanup

When importing from CSV:
1. Read with `csv.DictReader`
2. Filter out test/placeholder entries with explicit exclusion logic
3. Categorize by keyword matching on prompt content
4. Optionally clean typos via targeted string replacements
5. Write to sheet with color coding by category
