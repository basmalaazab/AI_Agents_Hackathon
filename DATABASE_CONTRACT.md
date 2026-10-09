# Database and API reference

Clearview BI uses SQLAlchemy models and a database configured through `DATABASE_URL`. The API is mounted below `/api/v1`; interactive OpenAPI documentation is available at `/docs` while the backend is running. Business endpoints require a bearer session token returned by sign-up or login.

## Data model

| Table | Purpose | Key fields and behavior |
| --- | --- | --- |
| `workspaces` | Company boundary | Company name and workspace ID |
| `app_users` | Company members | Email, full name, role, password hash and workspace ID |
| `auth_sessions` | Login sessions | Hashed bearer token and expiration |
| `workspace_invitations` | Pending team invites | Workspace, email, role, hashed one-time token and seven-day expiration |
| `audit_events` | Company account history | Workspace, optional user, event type, summary and timestamp |
| `data_sources` | Import and connector registry | Workspace, source name/type, display name and active flag |
| `customers` | Customer profiles | Source-scoped external identity and contact/profile fields |
| `orders` | Order attempts and sales | Source-scoped external ID, customer, date, status, original amount/currency and normalized USD amount |
| `order_items` | Products sold on an order | Order/product references, product snapshot, quantity, original line amount/currency and normalized USD amount |
| `products` | Catalog and optional inventory | Source-scoped external ID, name, SKU, category, price/currency, stock and reorder point |
| `ingestion_runs` | Pipeline audit trail | Source, record type, status, timestamps and fetched/valid/inserted/duplicate/invalid counts |
| `raw_records` | Ingested source payloads | Run, source, record type and original payload |
| `data_quality_errors` | Rows that failed validation | Run, record type, error details and source payload |
| `user_chat_messages` | Persisted analyst conversation | User, message, intent and optional result metadata |

Orders and products are deduplicated by source and external ID; source identities are not automatically matched across different platforms. Order/customer linkage may be absent if the related customer was not imported.

## Authentication and workspace isolation

- `POST /auth/signup` creates a company owner and workspace. On an existing database, the first account retains the seeded demo workspace; later signups receive isolated workspaces.
- `POST /auth/login` returns a bearer token; use `Authorization: Bearer <token>` for authenticated routes. Sessions expire after 14 days. `POST /auth/logout` revokes the current token.
- Managers can invite users as managers or viewers, change roles, remove members and revoke invitations. Invitations expire after seven days; SMTP is optional.
- Request dependencies scope ORM data access to the current user's workspace. Viewer access is read-only for imports and source changes.
- Direct SQL execution is disabled for workspace accounts; the `/agent/sql` endpoint returns a forbidden response. This prevents unfiltered ad-hoc SQL from bypassing application-level tenant scope.

## Currency normalization

`orders.total_amount` and `order_items.line_total` retain original amounts and ISO currency codes. `total_amount_usd` and `line_total_usd` hold normalized values for analytics. Rates are refreshed from the USD-based ExchangeRate-API endpoint at most once daily, with bundled reference rates retained when the service is unavailable. USD totals use the stored conversion at ingestion/backfill time; this is not a transaction-date FX ledger. If no rate is available, the normalized value stays empty, and the order is counted as unconverted rather than assumed to be USD. The dashboard and AI context disclose exclusions.

## Inventory and reorder drafts

Product imports may include `stock_quantity` and `reorder_point`, including common aliases such as `inventory_quantity`, `quantity_on_hand` and `low_stock_threshold`. Risk flags cover zero stock, stock at/below reorder point, or estimated cover of 14 days or less. Days-of-cover estimates use the latest 30 days of linked sales and do not model supplier lead time, reserved stock or safety stock.

`POST /agent/inventory-reorder-draft` takes `product_name`, optional `product_sku`, `source_name`, `supplier_lead_time_days` and optional `target_cover_days` (default 14). It calculates a suggested quantity from recent average daily sales and the requested cover period, subject to the imported reorder point. If evidence is insufficient, the result says so. The draft is a response only; it is not persisted and never places an order.

## AI answer and evidence flow

The built-in analytics logic prepares the baseline metrics and evidence before any language model is called. If `OPENAI_API_KEY` is set, OpenAI is attempted first; if that provider fails, configured Gemini is tried next. When no provider succeeds, the built-in analyst returns its deterministic answer. `POST /agent/query/stream` sends SSE events; the frontend renders answer chunks progressively. Responses include period/source context, evidence sufficiency and a metric snapshot. Recommendations are suggestions to validate, not guaranteed outcomes.

## API endpoints

All paths below are relative to `/api/v1`.

### Authentication and teams

| Method and path | Purpose |
| --- | --- |
| `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout` | Create account, start and revoke a session |
| `GET /auth/me` | Current member and company |
| `GET /auth/team` | Company members and pending invitations |
| `POST /auth/invitations`, `GET /auth/invitations/preview`, `POST /auth/invitations/accept` | Invite, preview and accept a team invitation |
| `PATCH /auth/team/{member_id}/role`, `DELETE /auth/team/{member_id}` | Change role or remove a member |
| `DELETE /auth/invitations/{invitation_id}` | Revoke a pending invite |
| `GET /auth/audit-events` | Recent workspace sign-in and account events |
| `GET/POST/DELETE /auth/chat-history` | Read, save or clear the member's analyst chat history |

### Data, pipelines and sources

| Method and path | Purpose |
| --- | --- |
| `POST /upload/csv` | Import `order`, `customer` or `product` CSV data |
| `GET/POST/DELETE /sources` | List, register or remove a source; registration alone does not test external access |
| `GET /sources/integration-readiness` | Check whether a Stripe credential is configured without returning it |
| `POST /pipelines/trigger` | Run a connector for a source and record type |
| `GET /pipelines/runs`, `GET /pipelines/runs/{run_id}`, `GET /pipelines/summary` | Review run details, history and ingestion totals |
| `GET /health` | API and database health |

### Analytics and exports

| Method and path | Purpose |
| --- | --- |
| `GET /analytics/overview` | KPI totals and period-over-period comparisons |
| `GET /analytics/revenue-trends` | Revenue, orders and average order value over time |
| `GET /analytics/sales-breakdown` | Categories, source platforms and top products |
| `GET /analytics/customers` | Customer activity, retention indicators and RFM segments |
| `GET /analytics/alerts`, `GET /analytics/inventory-risk` | Business alerts and stock-risk estimates |
| `GET /analytics/ai-context` | Structured workspace metrics and evidence for the analyst |
| `GET /analytics/export/csv` | Revenue and order time-series CSV |
| `GET /analytics/export/xlsx` | Executive workbook with summary, trends, products, customer segments and recommendations where available |

Analytics routes accept the selected date range and, where applicable, a source filter and custom dates.

### AI Analyst

| Method and path | Purpose |
| --- | --- |
| `POST /agent/query`, `POST /agent/query/stream` | Evidence-grounded answer, as a full response or SSE stream |
| `POST /agent/recommendations` | Prioritized business recommendations |
| `POST /agent/diagnose` | Evidence-based investigation of a business alert |
| `POST /agent/inventory-reorder-draft` | Review-only suggested restock quantity |
| `GET /agent/suggestions`, `GET /agent/capabilities` | Contextual prompts and capability metadata |
| `POST /agent/sql` | Disabled for authenticated workspaces |

## Connector status

Registered source types include `csv`, `spreadsheet`, `mock_api`, `stripe` and `hubspot`. Stripe uses `STRIPE_SECRET_KEY` on the backend and imports only records available to the configured account. HubSpot and other connectors depend on their own credentials and implementation. Do not treat a registered source as proof that credentials, permissions or an external sync succeeded; review the corresponding pipeline run.
