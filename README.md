# AI Business Intelligence Agent — Data Engineering & Integration Layer

> **Hackathon Track: Person 1 (Data Engineering and Data Integration)**  
> Built for the **AI Business Intelligence Agent for Small Businesses** project.

---

## 📖 Overview

Small businesses operate on fragmented tools (spreadsheets, POS systems, e-commerce stores, CRMs). This module builds the robust **Data Engineering Layer** that automatically ingests data from disparate sources, validates and cleans it, applies schema normalizations, prevents duplicate entries, logs data quality errors without dropping data, and persists everything into a centralized PostgreSQL database.

This module provides clean, tested tables and analytical endpoints for:
- **Person 2 (Analytics & KPI Dashboards):** Standardized orders, revenue aggregates, daily sales trends, and customer purchase frequency metrics.
- **Person 3 (AI Agent):** Safe, structured, read-only access to query operational business data and generate actionable recommendations.

---

## 🚀 Quick Start

### Option 1: Docker Compose (All-in-One: PostgreSQL + Mock API + App)

```bash
# 1. Enter project directory
cd ai-bi-agent

# 2. Copy environment variables
cp .env.example .env

# 3. Start containers
docker compose up --build
```
- **FastAPI API & Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Mock E-Commerce API:** [http://localhost:8001](http://localhost:8001)
- **PostgreSQL Database:** `localhost:5432` (`bi_db` / `bi_user` / `bi_password`)

---

### Option 2: Local Python Virtualenv

```bash
# 1. Create and activate virtual environment
cd ai-bi-agent
python -m venv .venv
.venv\Scripts\activate       # On Linux/macOS: source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database tables & seed sources
python scripts/init_db.py

# 4. Start the Mock API (Terminal 1)
uvicorn mock_api.main:app --host 0.0.0.0 --port 8001

# 5. Start the Main API (Terminal 2)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🏗️ Architecture & Pipeline Flow

```
┌─────────────────┐       ┌──────────────────────┐       ┌────────────────────────┐
│  Data Sources   │ ────► │ Ingestion & Raw Store │ ────► │ Validation & Error Log │
│ (CSV, Mock API, │       │  (raw_records table) │       │ (data_quality_errors)  │
│  Spreadsheet)   │       └──────────────────────┘       └───────────┬────────────┘
└─────────────────┘                                                  │
                                                                     ▼
┌─────────────────┐       ┌──────────────────────┐       ┌────────────────────────┐
│ Person 2 & 3:   │ ◄──── │ Clean DB Tables      │ ◄──── │ Cleaning, Normalizing, │
│ Analytics & AI  │       │ (customers, orders,  │       │ Deduplication & Load   │
│ Endpoints & SQL │       │  products, items)    │       │ (idempotent upserts)   │
└─────────────────┘       └──────────────────────┘       └────────────────────────┘
```

1. **Connectors:** Modular connector interface (`BaseConnector`) supports CSV uploads, mock REST APIs, and local spreadsheets.
2. **Raw Storage:** Original data payloads are preserved as JSON in `raw_records` for compliance and debugging.
3. **Validation:** Checks column requirements, formats, types, and ranges. Invalid records are rejected and logged in `data_quality_errors` with exact failure causes.
4. **Cleaning:** Normalizes column name variations (`sale_id` → `order_id`), trims whitespace, title-cases names, normalizes timestamps to UTC, and cleans currency strings.
5. **Deduplication:** Intra-batch duplicate detection + composite unique constraints `(source_name, external_id)` ensure rerunning a pipeline never creates duplicate business records.
6. **Central PostgreSQL DB:** Normalized relational schema with foreign keys, indexes, and UTC timestamps.

---

## 🗄️ Database Schema & Contract

Full interface contract documented in [`DATABASE_CONTRACT.md`](./DATABASE_CONTRACT.md).

### Tables Summary

| Table | Description | Primary Key | Identity / Uniqueness |
|---|---|---|---|
| `data_sources` | Configured ingestion platforms | `id` (UUID) | `name` UNIQUE |
| `ingestion_runs` | Execution audit log with status and record counters | `id` (UUID) | - |
| `raw_records` | Original raw JSON payloads | `id` (UUID) | Indexed on `ingestion_run_id` |
| `data_quality_errors` | Details on records failing validation | `id` (UUID) | Indexed on `error_type`, `run_id` |
| `customers` | Clean customer records | `id` (UUID) | UNIQUE `(source_name, external_id)` |
| `orders` | Clean sales and orders | `id` (UUID) | UNIQUE `(source_name, external_id)` |
| `order_items` | Line items belonging to orders | `id` (UUID) | FK `order_id`, FK `product_id` |
| `products` | Product catalog | `id` (UUID) | UNIQUE `(source_name, external_id)` |

---

## 📡 REST API Reference

Interactive Swagger documentation available at `http://localhost:8000/docs`.

### Ingestion & Pipeline Management
- `POST /api/v1/upload/csv` — Multipart CSV upload for `customer`, `order`, or `product` records.
- `GET /api/v1/sources` — List all registered data sources.
- `POST /api/v1/sources` — Register a new source.
- `POST /api/v1/pipelines/trigger` — Trigger ingestion from an API-based source.
- `GET /api/v1/pipelines/runs` — View execution history with counters.
- `GET /api/v1/pipelines/summary` — Aggregate pipeline status.

### Clean Data Access & Analytics
- `GET /api/v1/data/customers` — Query clean customers.
- `GET /api/v1/data/orders` — Query clean orders.
- `GET /api/v1/data/products` — Query clean products.
- `GET /api/v1/data/quality-errors` — View failed records with raw payloads.
- `GET /api/v1/data/analytics/revenue-summary` — Precomputed total orders, total revenue (USD), AOV.
- `GET /api/v1/data/analytics/sales-by-date` — Daily sales trends.
- `GET /api/v1/data/analytics/sales-by-product` — Units sold & revenue per product.
- `GET /api/v1/data/analytics/customer-frequency` — Customer order counts & lifetime value.

---

## 🧪 Demo Dataset & Verification

Sample data files are provided in [`data/`](./data/):
- `data/sample_customers.csv`: 14 synthetic customer records containing intentional duplicates, bad emails, missing fields, and case inconsistencies.
- `data/sample_sales.csv`: 21 synthetic sales records containing intentional duplicates, negative totals, invalid dates, and mixed currency formatting.

### Run Automated Demo Verification:
```bash
python scripts/verify_demo.py
```
This script runs a complete live simulation:
1. Ingests dirty customer CSV (12 inserted, 1 duplicate removed, 1 invalid logged).
2. Ingests dirty sales CSV (17 inserted, 1 duplicate removed, 3 invalid logged).
3. Re-ingests sales CSV to verify **100% idempotent deduplication** (0 inserted, 18 duplicates).
4. Inspects logged data quality errors.
5. Queries KPI analytics endpoints.

---

## 🔬 Test Suite

Run the full automated test suite (65 passing unit and integration tests):

```bash
pytest -v
```

```
tests/unit/test_cleaner.py (26 tests) .......................... PASSED
tests/unit/test_deduplication.py (5 tests) .....                 PASSED
tests/unit/test_validator.py (13 tests) .............            PASSED
tests/integration/test_ingestion_workflow.py (9 tests) ......... PASSED
tests/integration/test_api_endpoints.py (6 tests) .............. PASSED

======================== 65 passed in 1.43s ========================
```

---

## ⚙️ Technology Stack & Tradeoffs

| Component | Choice | Rationale |
|---|---|---|
| **API** | FastAPI + Pydantic | Fast, async, automated OpenAPI docs |
| **Database** | PostgreSQL 16 | ACID-compliant, JSONB support, robust indexing |
| **ORM** | SQLAlchemy 2.0 | Type-safe declarative models & cross-dialect testing |
| **Data Processing** | Pandas + NumPy | Vectorized validation & column transformations |
| **Scheduler** | APScheduler | Lightweight, zero external service dependency for MVP |
| **Optional: Airflow** | Extension Ready | Replace `scheduler.py` with Airflow DAG when scaled |
| **Optional: dbt** | Extension Ready | Use clean tables as staging models for dbt marts |
| **Optional: Airbyte** | Extension Ready | Can write directly into `raw_records` via webhook |
