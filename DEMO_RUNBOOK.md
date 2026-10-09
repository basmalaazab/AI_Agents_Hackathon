# Clearview BI — online demo runbook

This guide is for a short, self-guided hackathon demo. The product presentation is an online submission for reviewers to browse; it does not assume a live pitch or a person narrating it.

## Demo setup

For a one-command Docker setup, start Docker Desktop and run `.scriptsjudge_demo.ps1` from the repository root in PowerShell. Open the printed local URL and create a company account. The script seeds the isolated judge workspace and requires no AI provider key. Stop it with `.scriptsjudge_demo.ps1 -Stop`; the data volume remains available. A first-time container build depends on network and machine speed.

Use a disposable database to make the walkthrough predictable. From the repository root in PowerShell:

```powershell
$env:DATABASE_URL = "sqlite:///./hackathon_demo.db"
$env:SCHEDULER_INTERVAL_MINUTES = "0"
.\.venv\Scripts\python.exe scripts\seed_demo_analytics.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal, start the frontend using [the local setup instructions](README.md#run-locally-on-windows). Create the demo company account, or log in to the prepared demo workspace. The first account on a seeded database claims the demo workspace; later accounts use isolated workspaces.

The supplied sample figures and CSVs are fictional. Keep them separate from any real company data.

## Impact evidence and limits

The dashboard's revenue, order, cancellation and stock figures come from synthetic sample records. They demonstrate what the product calculates, not business outcomes achieved for an SME. No real SME pilot has yet measured hours saved, operating cost saved or incremental revenue. For a real pilot, record a baseline and post-use measurement for the same reporting workflow, and attribute any change carefully before making an impact claim.

For a realistic public-data walkthrough, import the prepared UCI CSVs described in [the data guide](data/README.md#public-historical-retail-sample-uci). The historical rows support sales, product and customer analysis, but contain no inventory balances and cannot establish Clearview's impact on the original retailer.

## Self-guided product path

1. **Overview:** choose the 30-day period. Review revenue, order volume, cancellation alerts, top products and the low-stock monitor. Explain the figures as sample data, not real business results.
2. **AI Analyst:** ask, “Is our top product at risk of running out of stock?” The answer should use available stock and sales data, name its period and source, and indicate what it cannot establish.
3. **Restock draft:** open the suggested reorder draft for the flagged product. Enter supplier lead time if known, review the calculated target and suggested quantity, and note that the app does not submit a purchase order.
4. **Customer segments:** inspect RFM segments and the suggested action for each group. Segmentation depends on having adequate customer and order history.
5. **Reports:** download the Excel workbook or open the print/PDF report. Confirm the selected period and source filters before exporting.
6. **Data Sources and Activity:** import an example CSV or inspect a completed pipeline run. A Stripe source needs a server-side test key and sample records in the Stripe test account. A completed sync that fetches zero records can still validate access; show its run details and avoid presenting it as fresh sales data.
7. **Team:** invite a second email as a viewer. With SMTP configured, the app sends an invitation; otherwise copy the seven-day link and accept it in another browser profile. Confirm both members see the same company workspace and the viewer cannot import or sync.

## Example questions

- “What changed in revenue compared with the previous period?”
- “Which products generated the most revenue and units sold?”
- “Is our top product at risk of running out of stock?”
- “How many customers are in each RFM segment, and what should we do next?”
- “Give me three prioritized recommendations to increase revenue.”

Choose questions supported by the imported records. If the answer indicates insufficient coverage, that is the intended behavior: the analyst should not invent a cause, metric or customer fact.

## What the demo demonstrates

Clearview BI combines company-scoped data imports, analytics, audit history, inventory alerts, RFM customer groups, streaming AI answers and report exports. The AI provider order is OpenAI followed by Gemini when both keys are configured; if neither provider is available, the built-in analyst still responds. Recommendations are starting points for human review.

## Integration and data notes

- The Stripe connector requires `STRIPE_SECRET_KEY` in the backend environment. Never place the secret in the browser or in a slide/document. Use a restricted Stripe test-mode key for the demo.
- Stripe can sync only records available to the account. If it returns zero fetched rows, the dashboard should continue using the imported demo dataset.
- Supported source currencies are converted to USD with daily reference rates when available; unknown currencies are excluded and disclosed. This is not transaction-date accounting FX.
- Inventory estimates rely on imported stock and recent linked sales; they do not include supplier lead time or safety stock automatically.
- Clearview BI has not measured real customer outcomes. Present benefits as intended outcomes, not proven impact.

## Before sharing or using live data

Use HTTPS and a managed production database, review workspace authorization and secret handling, configure backups and retention, monitor API provider usage, and rotate any credential that has been shared. The current build is a hackathon/MVP, not a production financial reporting system.
