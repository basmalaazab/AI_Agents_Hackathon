# Clearview BI — frontend

The frontend is a React 19 and TypeScript single-page application built with Vite. It calls the FastAPI backend for authentication, company-scoped analytics and ingestion. Third-party API keys belong only in the backend environment.

## Start the development server

From this directory:

```bash
npm ci
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Start the API separately by following the repository [local setup](../README.md#run-locally-on-windows). Vite proxies `/api` to `http://127.0.0.1:8003`; set `VITE_PROXY_TARGET` before startup to use another backend.

## User-facing areas

- **Overview:** date and source filters, KPI comparisons, revenue trends, category and channel breakdowns, alerts, product/customer summaries, inventory cover and customer segments.
- **AI Analyst:** streamed chat, recommendations, anomaly diagnosis and inventory reorder drafts. Answers show their period and source scope and identify evidence limitations.
- **Data Sources:** registered sources, CSV import, connector readiness and sync history.
- **Team:** company members, invitations and manager/viewer roles.
- **Activity:** ingestion runs and account audit events, including sign-ins and team changes.
- **Reports:** Excel workbook export, printable executive report/PDF and CSV trend export.

## Configuration and implementation notes

- `VITE_PROXY_TARGET` is a development proxy target, not a production API URL setting.
- Store `STRIPE_SECRET_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, SMTP and other credentials in the backend environment only.
- Revenue is displayed in USD. Supported currencies are normalized using daily reference rates; unknown currencies are excluded from revenue and identified in the dashboard. The conversion is not historical accounting FX.
- Inventory cover uses imported stock and recorded linked sales; the estimate does not include supplier lead time. Reorder drafts are for review and do not place orders.
- Each user session is associated with a company workspace. Viewer controls do not allow imports or connector syncs.
- Styling tokens and responsive behavior live in `src/index.css`.

## Checks

```bash
npm run lint
npm run build
```
