# Clearview BI

Clearview BI is a business analytics demo for small businesses. It brings sales, customer, and product records into one database, shows key performance metrics, and lets owners ask questions about the data in English or Arabic.

> **Demo data:** The included sample data is fictional. Treat dashboard values as examples unless you have imported your own records.

## What you can do

- Import order, customer, and product CSV files. The pipeline checks required fields, cleans common formats, skips duplicates, and records invalid rows for review.
- View revenue and order trends, category and source breakdowns, customer metrics, top products, and business alerts.
- Ask the built-in analyst questions about revenue, orders, products, customers, trends, and recommendations. The deterministic analyst works without an external AI key.
- Optionally enhance answers with OpenAI and use Gemini as a fallback by configuring server-side API keys.
- Inspect read-only SQL results where supported by the analyst.

## Data sources and current limits

The project includes CSV, spreadsheet, mock API, Stripe, and HubSpot connector implementations. Stripe and HubSpot require valid server-side credentials. Registering a source does not by itself guarantee that the external service is connected or that synchronization will succeed. Shopify, social media, and customer-support integrations are not implemented in this version.

This is a hackathon/MVP build, not a production-ready financial system. Revenue analytics are in USD; non-USD orders are excluded because no exchange-rate conversion is configured. Product inventory can be imported and stock cover is estimated from the last 30 days of linked sales. The estimate does not include supplier lead time or safety stock. Cross-platform customer identity matching is not implemented. The Activity tab is a placeholder.

Company accounts are enabled: the first account on an existing database keeps the current demo workspace, and each later signup creates a separate workspace. Company managers can invite teammates from the Team tab and assign manager or viewer access. SMTP settings enable email delivery; without SMTP, the app creates a secure seven-day invitation link to copy and send. Viewers can inspect dashboard and analyst results but cannot import data, manage sources, or sync connectors. Direct SQL access remains disabled so it cannot bypass workspace filters.

The Stripe connector uses a server-side `STRIPE_SECRET_KEY`. Add a restricted Stripe test key to the backend environment, register a Stripe source under Data Sources, and choose **Sync Stripe**. The app imports customers, products, and payments through the existing pipeline and shows the latest run status. Never paste the key into the browser or commit it.

## Run locally

Requirements: Python 3.11 or newer and Node.js with npm.

### 1. Start the API

From the repository root, create and activate a virtual environment, then install the Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DATABASE_URL = "sqlite:///./local_runtime.db"
$env:SCHEDULER_INTERVAL_MINUTES = "0"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs). Keep this terminal open.

### 2. Start the web app

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite development server proxies API requests to the local backend.

### Optional: use external AI providers

Set `OPENAI_API_KEY` and/or `GEMINI_API_KEY` in the backend environment or an untracked local `.env` file. The backend tries OpenAI first, then Gemini, and falls back to the built-in analyst if neither provider responds. When enabled, the analytics context and question are sent to the selected provider. Keep keys out of the frontend and never commit `.env`.

### Docker Compose

With Docker installed and running, start the bundled PostgreSQL database, mock API, backend, and frontend:

```bash
docker compose up --build
```

The Compose backend uses PostgreSQL; the local-development commands above use SQLite.

## How to use the app

1. Choose a date range and, if needed, filter by a registered source.
2. Review the KPI cards, trend chart, category/source breakdowns, products, and alerts.
3. Ask the AI Business Analyst a specific question, such as “Why did revenue change this month?”
4. Open **Data Sources** to upload CSV records or register an available connector. Check the pipeline result before relying on newly imported data.
5. To demonstrate stock-risk analysis, seed synthetic recent sales using PowerShell:

   ```powershell
   $env:DATABASE_URL = "sqlite:///./demo_runtime.db"
   $env:SCHEDULER_INTERVAL_MINUTES = "0"
   python scripts/seed_demo_analytics.py
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

   Stop any existing backend first, and keep this demo database separate from your own imported data. Then upload `data/sample_products.csv` as **Products** with source name `shopify_store`. The sample monitor is below its reorder point. Restart the backend after code updates so the API uses the latest changes.

## Checks

```powershell
cd frontend
npm run lint
npm run build
cd ..
$env:DATABASE_URL = "sqlite:///./test_runtime.db"
$env:SCHEDULER_INTERVAL_MINUTES = "0"
$env:OPENAI_API_KEY = ""
$env:GEMINI_API_KEY = ""
python -m pytest tests -q
```

The backend test suite includes API integration tests that bind to localhost.

## Project documentation

- [Database and API reference](DATABASE_CONTRACT.md)
- [Demo data notes](data/README.md)
- [Frontend development notes](frontend/README.md)
