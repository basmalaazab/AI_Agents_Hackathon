# Database Contract — AI BI Agent

> **Audience:** Person 2 (Analytics & Dashboard) and Person 3 (AI Agent)
> **Maintained by:** Person 1 (Data Engineering)
> **Last updated:** 2024-10

This document defines the stable database interface that downstream components can rely on.

---

## Connection Details

| Setting | Value |
|---------|-------|
| Host | `localhost` (or `postgres` inside Docker) |
| Port | `5432` |
| Database | `bi_db` |
| User | `bi_user` |
| Password | `bi_password` (set in `.env`) |
| Connection string | `postgresql://bi_user:bi_password@localhost:5432/bi_db` |

**Python (SQLAlchemy):**
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://bi_user:bi_password@localhost:5432/bi_db")
```

**Read-only access for AI agent:** Use the same credentials but execute only `SELECT` statements. A dedicated read-only role can be created by running:
```sql
CREATE ROLE bi_reader WITH LOGIN PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE bi_db TO bi_reader;
GRANT USAGE ON SCHEMA public TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bi_reader;
```

---

## Clean Business Tables

These are the primary tables for analytics and AI queries.

### `customers`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Internal surrogate key |
| `source_name` | VARCHAR(120) | Data source name (e.g. `csv_upload`, `mock_ecommerce_api`) |
| `external_id` | VARCHAR(255) | ID from the source system |
| `email` | VARCHAR(255) | Cleaned, lowercased email address |
| `first_name` | VARCHAR(120) | Title-cased first name |
| `last_name` | VARCHAR(120) | Title-cased last name |
| `phone` | VARCHAR(50) | Phone number as provided |
| `city` | VARCHAR(120) | Title-cased city |
| `country` | VARCHAR(120) | Title-cased country |
| `created_at` | TIMESTAMPTZ | Record creation time (UTC) |
| `updated_at` | TIMESTAMPTZ | Last update time (UTC) |

**Unique constraint:** `(source_name, external_id)`

> ⚠️ Cross-platform identity resolution is NOT implemented. A customer on platform A and the same person on platform B will appear as two separate rows. Do NOT assume two rows with the same email are the same customer without additional verification.

---

### `orders`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Internal surrogate key |
| `source_name` | VARCHAR(120) | Data source |
| `external_id` | VARCHAR(255) | Order ID from source system |
| `customer_id` | UUID (FK → customers.id) | Linked customer (nullable) |
| `order_date` | TIMESTAMPTZ | Order timestamp (UTC) |
| `status` | VARCHAR(50) | `completed`, `pending`, `cancelled`, `refunded` |
| `total_amount` | NUMERIC(12,2) | Order total in original currency |
| `currency` | CHAR(3) | ISO currency code (e.g. `USD`, `GBP`) |
| `total_amount_usd` | NUMERIC(12,2) | Amount normalised to USD (MVP: same as total_amount, FX conversion is a future extension) |
| `created_at` | TIMESTAMPTZ | Record creation time |
| `updated_at` | TIMESTAMPTZ | Last update time |

**Unique constraint:** `(source_name, external_id)`

---

### `order_items`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Internal surrogate key |
| `order_id` | UUID (FK → orders.id) | Parent order |
| `product_id` | UUID (FK → products.id, nullable) | Linked product (if resolved) |
| `product_name` | VARCHAR(255) | Product name as ingested |
| `sku` | VARCHAR(120) | Stock-keeping unit |
| `quantity` | INTEGER | Units purchased |
| `unit_price` | NUMERIC(12,2) | Price per unit |
| `line_total` | NUMERIC(12,2) | `quantity × unit_price` |
| `currency` | CHAR(3) | ISO currency code |

---

### `products`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Internal surrogate key |
| `source_name` | VARCHAR(120) | Data source |
| `external_id` | VARCHAR(255) | Product ID from source system |
| `name` | VARCHAR(255) | Product name |
| `sku` | VARCHAR(120) | SKU |
| `category` | VARCHAR(120) | Product category |
| `description` | TEXT | Product description |
| `unit_price` | NUMERIC(12,2) | Standard price |
| `currency` | CHAR(3) | ISO currency code |

**Unique constraint:** `(source_name, external_id)`

---

## Pipeline / Audit Tables

These tables are managed by the data engineering layer. Analytics and AI components should treat them as read-only reference data.

### `data_sources` — registered ingestion sources
### `ingestion_runs` — one row per pipeline execution
### `raw_records` — original JSON payloads (for debugging)
### `data_quality_errors` — validation failures with raw_data for inspection

---

## Example SQL Queries

### Total revenue (excluding cancelled/refunded)
```sql
SELECT
    COUNT(*) AS total_orders,
    SUM(total_amount_usd) AS total_revenue_usd,
    AVG(total_amount_usd) AS avg_order_value_usd
FROM orders
WHERE status NOT IN ('cancelled', 'refunded');
```

### Daily sales trend
```sql
SELECT
    DATE(order_date AT TIME ZONE 'UTC') AS sale_date,
    COUNT(*) AS order_count,
    SUM(total_amount_usd) AS revenue_usd
FROM orders
WHERE status NOT IN ('cancelled', 'refunded')
GROUP BY sale_date
ORDER BY sale_date DESC;
```

### Top products by revenue
```sql
SELECT
    oi.product_name,
    SUM(oi.quantity) AS units_sold,
    SUM(oi.line_total) AS revenue_usd
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY oi.product_name
ORDER BY revenue_usd DESC
LIMIT 10;
```

### Customer purchase frequency
```sql
SELECT
    c.email,
    c.first_name,
    c.last_name,
    COUNT(o.id) AS order_count,
    SUM(o.total_amount_usd) AS lifetime_value_usd
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY c.id, c.email, c.first_name, c.last_name
ORDER BY lifetime_value_usd DESC;
```

### Sales by product category
```sql
SELECT
    p.category,
    COUNT(oi.id) AS line_items,
    SUM(oi.line_total) AS revenue_usd
FROM order_items oi
JOIN products p ON p.id = oi.product_id
JOIN orders o ON o.id = oi.order_id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY p.category
ORDER BY revenue_usd DESC;
```

---

## REST API Data Access (Alternative to Direct SQL)

The data engineering service exposes read-only HTTP endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/data/customers` | Paginated clean customer records |
| `GET /api/v1/data/orders` | Paginated clean order records |
| `GET /api/v1/data/products` | Clean product catalogue |
| `GET /api/v1/data/analytics/revenue-summary` | Aggregate revenue KPIs |
| `GET /api/v1/data/analytics/sales-by-date` | Daily revenue series |
| `GET /api/v1/data/analytics/sales-by-product` | Revenue by product |
| `GET /api/v1/data/customer-frequency` | Customer purchase frequency |

### Person 2 Analytics APIs (Built for Dashboard & Person 3 AI Agent)

| Endpoint | Description | Query Parameters |
|----------|-------------|------------------|
| `GET /api/v1/analytics/overview` | Executive KPI cards with period-over-period comparison | `date_range`, `source_name`, `start_date`, `end_date` |
| `GET /api/v1/analytics/revenue-trends` | Time-series daily/monthly revenue & order volume | `date_range`, `source_name`, `start_date`, `end_date` |
| `GET /api/v1/analytics/sales-breakdown` | Category breakdown, sales channel share, & top products | `date_range`, `source_name`, `start_date`, `end_date` |
| `GET /api/v1/analytics/customers` | Customer growth, repeat rate, frequency cohorts, & top LTV | `date_range`, `source_name`, `start_date`, `end_date` |
| `GET /api/v1/analytics/alerts` | Automated business anomaly detection signals | `date_range`, `source_name`, `start_date`, `end_date` |
| `GET /api/v1/analytics/ai-context` | **Person 3 AI Agent Dataset Payload** (unified JSON for LLM reasoning) | `date_range`, `source_name`, `start_date`, `end_date` |
| `GET /api/v1/analytics/export/csv` | Downloadable CSV analytics report | `date_range`, `source_name`, `start_date`, `end_date` |

Base URL: `http://localhost:8000`


---

## Data Quality Notes

- Records failing validation are logged in `data_quality_errors` and are never silently discarded.
- Duplicate records from re-ingestion are skipped (idempotent pipeline).
- `total_amount_usd` is currently equal to `total_amount` — FX conversion is a recommended extension.
- `customer_id` in orders may be NULL if the customer record was not ingested before the order.
- Cross-platform customer identity resolution is out of scope for the MVP.
