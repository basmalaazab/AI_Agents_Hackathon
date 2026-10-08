# Clearview BI web app

The frontend is a React and TypeScript single-page application built with Vite. It displays business analytics and calls the FastAPI backend; it does not connect to third-party business platforms directly.

## Start the development server

From this directory:

```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite server proxies `/api` requests to `http://localhost:8000` by default. Start the backend separately; see the repository [Quick Start](../README.md#run-locally).

To use a different backend, set `VITE_PROXY_TARGET` before starting Vite.

## Available checks

```bash
npm run lint
npm run build
```

The build runs TypeScript project checks and creates static files in `dist/`.

## Main interface areas

- **Overview:** date/source filters, AI question box, business and low-stock alerts, KPI cards, charts, stock cover estimates, and top products/customers.
- **AI Analyst:** entry to the conversational analyst, recommendations, diagnostics, and read-only SQL results.
- **Data Sources:** CSV import, source registration, and pipeline status.
- **Activity:** placeholder until an activity-feed API is implemented.

Colors and typography are defined in `src/index.css`; chart colors should use the same design tokens. Product CSVs can provide `stock_quantity` and `reorder_point`. Stock cover is an estimate from the last 30 days and excludes supplier lead time. Non-USD orders are excluded from USD revenue totals because no conversion is performed.
