# OKF v0.2 Bundle Navigation

The `fc-plus-okf/` directory is an OKF v0.2 knowledge bundle. Structure:

- `index.md` — top-level, lists subfolders (meetings/, architecture/, financials/, data-exports/, database/, media/, references/)
- `<subfolder>/index.md` — lists all concepts in that folder with one-line descriptions
- `<concept>.md` — each concept has YAML frontmatter with `resource:` pointing to the real source file

## Key Concepts (as of Jul 2026)

### Hosting & Architecture (from meetings)
- Primary stack: AWS EC2 + Python + Chainlit + DuckDB + Xero API
- Production deployment documented in `fc-plus-environment-configuration-deployment-1-docx.md` (AWS SSM Parameter Store + KMS for secrets)
- Dashboards: Plotly Dash over Excel workbook (transitional toward dynamic DuckDB source)
- Two dashboards: Cash Flow Dashboard and Sellerboard Dashboard
- Xero ingestion is a separate OAuth 2.0 PKCE headless service producing DuckDB datasets

### Finance
- Monthly cashflow forecast: two workbook versions (09.06 and 10.06) covering FORECASTED CF, MONTHLY CF, BUDGET, ACTUALS, Transaction sheets
- Cash Flow Tool Overview (Jul 20, 2026 handover): Plotly Dash with 7 areas including Forecast Simulator

### Database (xero.duckdb)
- 26 tables in `xero_data` schema, plus audit and report tables
- Key tables: invoices (17,988), bank_transactions (9,595), payments (8,123), credit_notes (1,732), manual_journals (664), contacts, accounts, organisations
- Views: v_invoice_line_items, v_profit_and_loss, v_balance_sheet, v_trial_balance