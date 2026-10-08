# Database and API Reference

This document describes the data model and analytics endpoints currently used by Clearview BI. The database is managed through SQLAlchemy models; the exact database URL is configured with `DATABASE_URL`.

## Core tables

| Table | Purpose | Important fields |
| --- | --- | --- |
| `customers` | Customer records from each source | `source_name`, `external_id`, contact and location fields |
| `orders` | Sales orders and their status | `source_name`, `external_id`, `customer_id`, `order_date`, `status`, `total_amount`, `currency`, `total_amount_usd` |
| `order_items` | Products and quantities on an order | `order_id`, `product_id`, `product_name`, `sku`, `quantity`, `unit_price`, `line_total`, `currency` |
| `products` | Product catalog and optional inventory balances | `source_name`, `external_id`, `name`, `sku`, `category`, `unit_price`, `currency`, `stock_quantity`, `reorder_point` |
| `data_sources` | Registered import or connector sources | `name`, `source_type`, `is_active` |
| `ingestion_runs` | Pipeline run status and record counts | source, status, timestamps, fetched/inserted/duplicate/invalid counts |
| `raw_records` | Original ingested payloads for audit/debugging | run, source, record type, raw payload |
| `data_quality_errors` | Validation failures retained for review | run, record type, error details, raw payload |
| `workspaces` | Company data boundary | company name, workspace ID |
| `app_users` | Company members and assigned role | email, role, workspace ID, password hash |
| `auth_sessions` | Revocable, expiring login sessions | user ID, token hash, expiration |
| `workspace_invitations` | Single-use invitations that expire after seven days | workspace, email, role, token hash, expiration, acceptance time |

Orders and products are unique by `(source_name, external_id)`. A customer appearing in multiple source systems is not automatically matched to a single identity. `customer_id` on an order may be empty if its customer record was not ingested.

## Currency and inventory limitations

The pipeline does not perform exchange-rate conversion. Only USD orders are included in revenue totals; orders in other currencies are excluded and surfaced in the AI context. Existing databases clear the incorrectly inferred USD value on non-USD orders at startup.

Product CSV imports accept optional `stock_quantity` and `reorder_point` fields (also common aliases such as `inventory_quantity`, `quantity_on_hand`, and `low_stock_threshold`). The inventory-risk estimate uses the last 30 days of linked sales and flags zero stock, stock at/below reorder point, or estimated cover of 14 days or less. It does not account for reserved stock, supplier lead time, or safety stock.

The analyst can prepare a review-only restock draft with `POST /api/v1/agent/inventory-reorder-draft`. The request supplies the product, source, supplier lead time, and extra cover days. The target stock is the greater of `ceil(last-30-day average daily sales × (lead time + extra cover))` and the imported reorder point; the suggested quantity is `max(target stock − current stock, 0)`. If there are no eligible sales, the imported reorder point can only restore stock to that point; without either sales or a reorder point, the API reports insufficient data. Drafts are not saved and no purchase order is submitted.

## Analytics endpoints

All endpoints are under `/api/v1` and accept date/source filters where applicable.

| Endpoint | Purpose |
| --- | --- |
| `GET /analytics/overview` | KPI summary and period comparison |
| `GET /analytics/revenue-trends` | Revenue, orders, and average order value over time |
| `GET /analytics/sales-breakdown` | Product category, source, and top-product breakdowns |
| `GET /analytics/customers` | Customer activity and repeat-purchase metrics |
| `GET /analytics/alerts` | Business anomaly alerts |
| `GET /analytics/inventory-risk` | Stock levels and estimated days of cover |
| `GET /analytics/ai-context` | Structured analytics context for the business analyst |
| `GET /analytics/export/csv` | Download analytics as CSV |
| `POST /agent/inventory-reorder-draft` | Calculate a restock draft for human review; does not submit an order |
| `GET /sources` | List registered data sources |
| `GET /sources/integration-readiness` | Report whether the backend has a Stripe key configured; does not expose the key |
| `POST /sources` | Register a supported source type |
| `GET /pipelines/summary` | Ingestion run and record totals |
| `POST /pipelines/trigger` | Run ingestion; send `source_id` and `record_type` in the request body |
| `GET /pipelines/runs` | List recent ingestion runs |
| `POST /upload/csv` | Upload and ingest a CSV file |
| `GET /health` | API and database health |
| `POST /auth/invitations` | Manager-only invitation; sends email when SMTP is configured and otherwise returns a secure share link |
| `GET /auth/team` | List company members and pending invitations |
| `GET /auth/invitations/preview` | Validate an invitation link and show its company and role |
| `POST /auth/invitations/accept` | Accept an invitation and create a manager or viewer account in that workspace |
| `PATCH /auth/team/{member_id}/role` | Manager-only role update |
| `DELETE /auth/team/{member_id}` | Manager-only member removal |
| `DELETE /auth/invitations/{invitation_id}` | Manager-only invitation revocation |

For request/response schemas and interactive examples, start the API and open `/docs`.

## Supported source types

The source registry contains `csv`, `spreadsheet`, `mock_api`, `stripe`, and `hubspot`. Stripe uses the backend-only `STRIPE_SECRET_KEY`; the Data Sources screen reports whether it is configured and shows recent ingestion runs. Source registration only creates a record; a sync must complete successfully to confirm access.

## Read-only SQL

Business APIs require a bearer session. Each account belongs to one company workspace; ORM reads are filtered to that workspace's data sources, while managers can invite additional users with manager or viewer roles. Viewer roles can read analytics but cannot upload data, change data sources, or start pipelines. Direct SQL execution is disabled for authenticated workspaces because arbitrary SQL cannot be tenant-filtered by ORM rules. AI responses include the analysis period, company source scope, record counts, and a data-sufficiency note.
