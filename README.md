# Clearview BI

**One clear view. Better next moves.**

Clearview BI is a multi-company business intelligence demo for startups and small businesses. It brings imported sales, customer, product and inventory data into a shared workspace, turns it into an operational dashboard, and provides an AI Business Analyst that answers from the available records.

> **Demo data:** The included CSVs and the sample figures in screenshots and the presentation are synthetic. They are for product demonstration only and are not customer results or financial guidance.

## At a glance

- **Bring data together:** upload order, customer and product CSVs; connect the Stripe test-mode connector when a server-side key is configured.
- **See business performance:** explore revenue and order trends, period comparisons, products, categories, sales sources, customer activity, alerts and inventory risk.
- **Ask the analyst:** get streamed answers grounded in workspace metrics, with the period and source scope shown and limitations called out when evidence is incomplete.
- **Use AI providers optionally:** OpenAI is tried first, Gemini is the fallback, and the built-in deterministic analyst remains available if providers are not configured or fail.
- **Move from alert to action:** review RFM customer segments and prepare an inventory reorder draft for a manager to review. Drafting never places an order.
- **Share a company workspace:** invite managers or viewers, keep each company's records scoped to its workspace, and review account and ingestion activity.
- **Export a report:** download a multi-sheet Excel workbook or use the print/PDF report view.
- **Normalize supported currencies:** revenue is reported in USD using daily reference rates when available. Orders with unsupported or unavailable rates are reported separately and excluded from USD totals.

## Product workflow

1. **Create a company account.** The first account on a fresh database claims the existing demo workspace; subsequent company signups receive separate workspaces.
2. **Import or connect data.** Upload CSVs from **Data Sources**, or configure a Stripe test key on the backend and sync a registered Stripe source. Review each pipeline run's result and timestamp.
3. **Explore the dashboard.** Select a period and source, review KPIs and alerts, then use the customer segments, product and inventory views to identify a question.
4. **Ask and act carefully.** Ask the AI Business Analyst for a measured explanation or recommendation. Use the evidence and caveats to judge the answer. A reorder draft is for human review; it does not create a purchase order.
5. **Share and report.** Invite a teammate with manager or viewer access, inspect activity, and export the current report.

## Features

### Data ingestion and quality

The pipeline validates and normalizes incoming records, stores source and raw payload context, skips duplicates, and records invalid rows and run counts. Order, customer and product imports are supported. Product files can include `stock_quantity` and `reorder_point` for stock-risk estimates.

### Analytics and inventory

Analytics include revenue, order count, average order value, active customers, prior-period comparisons, time trends, top products, sales channels, category breakdowns, customer activity and business alerts. Revenue conversions use refreshed daily reference rates with bundled rates as an offline fallback; this is not historical transaction-date FX accounting. Unsupported currencies are excluded from USD totals and surfaced in the UI/context. Inventory cover is estimated from linked recent sales and does not model supplier lead time unless a user supplies it when preparing a reorder draft.

### AI Business Analyst

The analyst first builds a deterministic answer from workspace-scoped metrics. If API keys are configured, it asks OpenAI to refine the answer and falls back to Gemini if OpenAI fails. If neither provider is available, the deterministic answer is used. The streaming endpoint sends answers over Server-Sent Events. The model receives the analytic context and draft answer; never place secrets in prompts or frontend code.

The analyst supports business questions, recommendations, anomaly diagnosis and inventory reorder drafts. It should state when records do not support an answer. Recommendations are suggestions to evaluate, not guaranteed business outcomes. Direct SQL execution is disabled for company workspaces.

### Company accounts and activity

Each account belongs to a company workspace. Managers can invite teammates and manage roles; viewers can read analytics but cannot import data, change sources or start syncs. Invitations last seven days. Configure SMTP to send invite email; without SMTP, the UI provides a secure invitation link to share. The Activity page combines ingestion history with account events such as sign-ins, invitations, role changes and member removal.

### Exports

- **Excel:** an executive summary plus sales trends, top products, customer segments and AI recommendations where available.
- **Print/PDF:** an executive report view suitable for browser printing or saving as PDF.
- **CSV:** time-series revenue and order data.

## Integrations and limits

- **CSV:** supported for orders, customers and products.
- **Stripe:** test/live API connector code is available; configure a restricted key on the backend. The connector imports only the records available to the account and permissions. A zero-record run can still validate access; check the run details and account data.
- **Other connector modules:** the repository includes connector foundations and optional integrations, but they are not all active, production-ready integrations. Do not assume Shopify, social media or customer-support systems are connected.
- **Cross-platform identity:** customer records are not automatically deduplicated across different platforms.
- **Currency:** only currencies with a known rate can be converted; the fallback reference rates are not a substitute for accounting FX.
- **Inventory:** estimates depend on imported stock and linked sales, and do not account for reserved units, supplier lead time or safety stock unless the user factors lead time into a draft.

This is a hackathon/MVP build. Before using live business data, review security, deployment configuration, access controls, backups, retention, monitoring, API-provider costs and financial reporting assumptions.

## Architecture

- **Frontend:** React, TypeScript and Vite single-page application (`frontend/`).
- **API:** FastAPI application with SQLAlchemy models and workspace-scoped analytics (`app/`).
- **Pipeline:** CSV and connector records pass through validation, normalization, deduplication and persistence (`app/pipeline/`, `app/services/`).
- **Storage:** PostgreSQL in Docker Compose; SQLite can be used for local development with `DATABASE_URL`.
- **Optional services:** mock API, Stripe, HubSpot, OpenAI, Gemini and SMTP, enabled through server-side environment settings.

See [Database and API reference](DATABASE_CONTRACT.md), [Demo runbook](DEMO_RUNBOOK.md), [demo data notes](data/README.md) and [frontend development notes](frontend/README.md).

## Requirements

- Python 3.11 or newer
- Node.js 22+ and npm (see the checked-in frontend lockfile)
- Docker Desktop with Compose, if using the container workflow

## Five-minute judge demo

With Docker Desktop running, open PowerShell in the repository root and run:

```powershell
.\scripts\judge_demo.ps1
```

The script starts an isolated Compose project on port `5175`, waits for the API health check, and loads the fictional demo dataset. Open the URL it prints and create a company account to claim the seeded workspace. The built-in analyst works without AI keys; OpenAI and Gemini are optional. Stop the demo with `.\scripts\judge_demo.ps1 -Stop`; its database volume is kept for the next run. The first image build may take longer than five minutes depending on network and machine speed; once images are cached, setup is a single command.

## Run locally on Windows

### 1. Start the API

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DATABASE_URL = "sqlite:///./local_runtime.db"
$env:SCHEDULER_INTERVAL_MINUTES = "0"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the API reference. Keep the API terminal running.

### 2. Start the frontend

In a second PowerShell terminal:

```powershell
cd frontend
$env:VITE_PROXY_TARGET = "http://127.0.0.1:8000"
npm ci
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies API requests to `http://127.0.0.1:8003` by default; the command above points it at the locally started API on port `8000`.

### Optional configuration

Copy `.env.example` to `.env` and set only the values you need. The backend loads `.env`; the frontend must never receive secret keys.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy database connection |
| `SCHEDULER_INTERVAL_MINUTES` | Automatic sync interval; use `0` to disable |
| `STRIPE_SECRET_KEY` | Server-side Stripe connector credential |
| `OPENAI_API_KEY` | Primary AI answer provider |
| `GEMINI_API_KEY` | Fallback AI answer provider |
| `HUBSPOT_ACCESS_TOKEN` | Optional HubSpot connector credential |
| `FRONTEND_BASE_URL` | Base URL used to construct invitation links |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` | Optional invitation email delivery |
| `MOCK_API_URL` | Mock API connector endpoint |

Never commit `.env`, paste secrets into the frontend, or use unrestricted keys. If a key has been shared publicly or in a chat, revoke it and create a replacement.

## Run with Docker Compose

With Docker Desktop running, from the repository root:

```powershell
docker compose up --build
```

Compose starts PostgreSQL, the mock API, the FastAPI backend and the Vite frontend. Open [http://localhost:5173](http://localhost:5173). To stop the stack, run `docker compose down`; the named PostgreSQL volume persists unless explicitly removed.

## Sample data

The `data/` folder contains fictional sales, customer and product examples. Follow the [demo data guide](data/README.md) to import them. Keep demo data in a separate database from any business records.

## Developer checks

```powershell
cd frontend
npm run lint
npm run build
cd ..
$env:DATABASE_URL = "sqlite:///./test_runtime.db"
$env:SCHEDULER_INTERVAL_MINUTES = "0"
python -m pytest tests -q
```

The backend test suite includes integration tests that bind to localhost. Use a disposable database for development checks.
