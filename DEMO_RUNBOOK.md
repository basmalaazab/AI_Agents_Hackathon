# Clearview BI hackathon demo

## Prepare a clean demo workspace

Use a disposable local database if you want a repeatable demo. From the repository root:

```powershell
$env:DATABASE_URL = "sqlite:///./hackathon_demo.db"
$env:SCHEDULER_INTERVAL_MINUTES = "0"
.\.venv\Scripts\python.exe scripts\seed_demo_analytics.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

In a second terminal, start the frontend using the [local setup instructions](README.md#run-locally). Open the app and create the demo company owner account. On an existing seeded database, the first account claims the demo workspace; later signups create isolated workspaces. Use a different database filename when you need a fresh demo.

## Demo path

1. **Overview:** Point out the revenue, orders, cancellation alert, and stock-risk estimate. Mention that the charts only use imported records and USD orders.
2. **AI Analyst:** Ask “Why is our cancellation rate high?” and show the period, source scope, record counts, and evidence sufficiency label under the response. If the note says the sample is limited, explain that the app avoids claiming a cause it cannot support.
3. **Data Sources:** Upload the provided CSV sample or register a Stripe source and run a sync with a backend-only Stripe test key. Show the timestamp and status of the latest pipeline run.
4. **Team:** Invite a second email as a viewer, copy and share the single-use link if SMTP is not configured, accept it in a second browser profile, and show the same company workspace. Demonstrate that viewer controls cannot upload or sync.

## Short presentation talk track

> Small businesses keep customer, order, payment, and inventory data in separate tools. That makes it hard to see what is changing and what needs attention. Clearview BI brings those records into one company workspace, checks and organizes imported data, and turns the resulting metrics into a business dashboard. Its analyst answers with the selected period, source scope, and record counts, and calls out when the sample is too small or missing. For the demo, I’ll show a sales alert, ask why the metric moved, sync a Stripe test account, and invite a teammate to view the same company data.

Avoid claiming that the current build automatically identifies causal factors from payment codes, provides currency conversion, or connects every advertised platform. The diagnosis summarizes measured changes and suggests checks; Stripe is the live API demonstration in this build, and non-USD orders remain excluded from USD revenue.

## Stripe setup

Set `STRIPE_SECRET_KEY` in the backend environment, restart the backend, register a Stripe source, then click **Sync Stripe**. Use a restricted test-mode key and a Stripe account containing test customers, products, and payments. A successful import creates separate audit runs for customers, products, and payments. If no key is set, the connector card explains what to configure.

## Invitation email setup

The invitation workflow always creates a seven-day, single-use invitation. Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM_EMAIL`, and, if required, `SMTP_USERNAME` / `SMTP_PASSWORD` on the backend to send invitation emails. Otherwise, copy the generated link and send it through your own email client.
