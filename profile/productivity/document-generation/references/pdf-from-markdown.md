# PDF Generation from Markdown (reportlab)

## Architecture

Parse markdown into structural elements → convert each to a reportlab flowable → build with SimpleDocTemplate.

## Available Python environments (macOS)

reportlab is often in the system Python but NOT the project venv. Check before writing scripts:

```bash
/opt/homebrew/bin/python3 -c "import reportlab; print('ok')"   # Homebrew Python
/usr/bin/python3 -c "import reportlab; print('ok')"             # System Python
.venv/bin/python -c "import reportlab; print('ok')"             # Project venv (often missing)
```

Write generation scripts to `/tmp/generate_report.py`, then run with whichever Python has reportlab:
```bash
/opt/homebrew/bin/python3 /tmp/generate_report.py
```

## Design System for Professional Reports

### Colors

| Element | Hex | Usage |
|---------|-----|-------|
| Dark navy | `#1e293b` | Table headers, H1/H2 text |
| Indigo | `#4f46e5` | Accent rules, left-border callouts, bullet colors |
| Indigo light | `#e0e7ff` | Total/summary row background |
| Slate | `#475569` | H3 text |
| Slate light | `#64748b` | Footer text, metadata |
| Border | `#cbd5e1` | Table grid lines |
| Row alt | `#f8fafc` | Even data rows |
| Green border | `#22c55e` | Slack/chat message blocks |
| Red | `#be123c` | Inline code styling |

### Fonts and Sizes

| Element | Font | Size |
|---------|------|------|
| H1 | Helvetica-Bold | 20pt |
| H2 | Helvetica-Bold | 14pt |
| H3 | Helvetica-Bold | 12pt |
| Body | Helvetica | 10.5pt, justified |
| Table header | Helvetica-Bold | 9.5pt |
| Table cell | Helvetica | 9.5pt |
| Footer | Helvetica | 8pt |
| Meta block | Helvetica | 9pt |

### Page Layout

- A4, margins: left/right 2cm, top 2.5cm, bottom 2cm
- Footer on pages 2+ only: "Page N" left, "Title — Confidential" right
- Footer separator line at 1.5cm from bottom (`#e2e8f0`, 0.5pt)

## Markdown Parsing Pattern

### Inline formatting

```python
def inline(text):
    """Convert markdown inline to reportlab markup."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)          # bold
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'<i>\1</i>', text)  # italic
    text = re.sub(r'`(.+?)`', r'<font face="Courier" size="8.5" color="#be123c">\1</font>', text)  # code
    return text
```

### Block detection (process line by line)

| Pattern | Element | Handling |
|---------|---------|----------|
| `# ` | H1 | Paragraph + 3pt indigo HR below |
| `## ` | H2 | Paragraph + 0.5pt light HR below |
| `### ` | H3 | Paragraph only |
| `\|---\|` | Table start | Collect all pipe-lines, parse cells, detect separator and total rows |
| `> [!NOTE]` | Note callout | Indigo left-border block |
| `> ` (text) | Blockquote / chat | Green left-border italic block |
| `* ` / `- ` | Bullet list | Accumulate, flush on blank line |
| `1. ` | Numbered list | Accumulate, flush on blank line |
| `---` | Horizontal rule | Thin border line + spacer |

### Table parsing

```python
# Collect all consecutive pipe-lines
cells = [c.strip() for c in line.strip("|").split("|")]
# Skip separator rows (all dashes/colons)
if all(re.match(r'^[-:]+$', c) for c in cells):
    continue
# Detect total row: any cell contains "total" (case-insensitive)
if any("total" in c.lower() for c in cells):
    total_row = cells  # style differently
```

### Table styling

```python
ts = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), C_DARK),           # dark header
    ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
])
# Alternating rows
for r_idx in range(1, len(data)):
    if r_idx % 2 == 0:
        ts.add("BACKGROUND", (0, r_idx), (-1, r_idx), C_ROW_ALT)
# Total row highlight
if total_row:
    total_idx = len(data) - 1
    ts.add("BACKGROUND", (0, total_idx), (-1, total_idx), C_TOTAL_BG)
```

### Column widths

```python
n_cols = len(rows[0])
col_widths = [17 * cm / n_cols] * n_cols  # 17cm available width on A4 with 2cm margins
```

### Footer function

```python
def add_footer(canvas, doc):
    canvas.saveState()
    page_num = canvas.getPageNumber()
    if page_num > 1:
        canvas.setStrokeColor(HexColor("#e2e8f0"))
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(HexColor("#64748b"))
        canvas.drawString(2 * cm, 1.1 * cm, f"Page {page_num}")
        canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, "Dreibach Ltd — Confidential")
    canvas.restoreState()

doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
```

## Complete script structure

1. Define colors (HexColor objects)
2. Define ParagraphStyle objects for each element type
3. Define `inline()` formatting function
4. Read and parse markdown line-by-line into flowables list
5. Define footer callback
6. Create SimpleDocTemplate and build

See `/tmp/generate_audit_pdf.py` in the session that created this skill for a full working example.

## Common report types

| Type | Layout notes |
|------|-------------|
| Financial audit | Multiple data tables, variance explanations, note callouts, executive summary |
| Executive summary | Minimal tables, mostly prose, clear section hierarchy |
| Technical review | Code blocks (Courier), risk tables, recommendation sections |
