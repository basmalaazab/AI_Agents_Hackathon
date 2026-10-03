# 🤖 AI Business Intelligence Agent for Small Businesses

> **Hackathon Project — Full-Stack AI Agent System**  
> A complete end-to-end platform that ingests messy business data, computes KPI analytics, and powers a conversational AI agent that lets business owners query their data in plain English.

---

## 👥 Team

| Person | Role | Scope |
|---|---|---|
| **Person 1 — Basmala** | Data Engineering & Integration | ETL pipelines, schema normalization, deduplication, PostgreSQL |
| **Person 2 — Shahd** | Analytics & KPI Dashboard | Metrics computation, React dashboard, interactive charts |
| **Person 3 — Sarah** | AI Business Intelligence Agent | NL query engine, SQL safety sandbox, anomaly diagnosis, strategic recommendations |

---

## 🏛️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES (Person 1)                               │
│   CSV Uploads │ Mock E-Commerce API │ Spreadsheets │ POS Systems             │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     ETL PIPELINE — Person 1                                  │
│  Ingest → Validate → Clean → Deduplicate → Load                              │
│  • raw_records (original JSON preserved)                                     │
│  • data_quality_errors (logged, not dropped)                                 │
│  • Clean tables: customers, orders, order_items, products                    │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
┌───────────────────────────┐  ┌────────────────────────────────────────────┐
│  ANALYTICS ENGINE          │  │  AI AGENT ENGINE — Person 3                │
│  Person 2                  │  │  • Natural Language Query Processing        │
│  • KPI computation         │  │  • 9 intent classifiers                    │
│  • Revenue / AOV / Churn   │  │  • SQL Safety Sandbox (read-only)          │
│  • Daily trends            │  │  • Anomaly Diagnosis                       │
│  • Customer health         │  │  • Strategic Recommendations               │
└───────────┬───────────────┘  │  • Optional LLM synthesis (Gemini/OpenAI)  │
            │                  └──────────────────┬─────────────────────────┘
            │                                     │
            └──────────────┬──────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    REACT DASHBOARD — Person 2 & 3                            │
│  KPI Cards │ Revenue Charts │ Product Performance │ AI Copilot Chat Modal   │
│  Recommendations Tab │ Anomaly Diagnosis │ Safe SQL Runner                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended — All-in-One)

```bash
cd ai-bi-agent
cp .env.example .env          # Copy env vars (add API keys for LLM features)
docker compose up --build
```

| Service | URL |
|---|---|
| FastAPI Backend + Swagger | http://localhost:8000/docs |
| React Dashboard | http://localhost:5173 |
| Mock E-Commerce API | http://localhost:8001 |
| Health Check | http://localhost:8000/api/v1/health |

### Option 2: Local Development

```bash
cd ai-bi-agent

# --- Backend ---
python -m venv .venv
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # Linux/macOS

pip install -r requirements.txt
python scripts/init_db.py        # Initialize DB + seed data sources

# Terminal 1: Mock API
uvicorn mock_api.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Main API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# --- Frontend ---
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

---

## 🗄️ Database Schema

Full interface contract: [`ai-bi-agent/DATABASE_CONTRACT.md`](./ai-bi-agent/DATABASE_CONTRACT.md)

| Table | Description |
|---|---|
| `data_sources` | Registered ingestion platforms |
| `ingestion_runs` | Execution audit log (status, record counters) |
| `raw_records` | Original raw JSON payloads (preserved for compliance) |
| `data_quality_errors` | Records failing validation with exact failure cause |
| `customers` | Clean, deduplicated customer records |
| `orders` | Clean, normalized sales & orders |
| `order_items` | Line items with FK to orders & products |
| `products` | Product catalog |

---

## 📡 API Reference

Interactive Swagger docs at `http://localhost:8000/docs`.

### Person 1 — Data Ingestion & Pipeline

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/upload/csv` | Upload CSV (customers, orders, or products) |
| `GET` | `/api/v1/sources` | List registered data sources |
| `POST` | `/api/v1/sources` | Register a new source |
| `POST` | `/api/v1/pipelines/trigger` | Trigger API-based ingestion |
| `GET` | `/api/v1/pipelines/runs` | Execution history |
| `GET` | `/api/v1/pipelines/summary` | Aggregate pipeline status |
| `GET` | `/api/v1/data/customers` | Query clean customers |
| `GET` | `/api/v1/data/orders` | Query clean orders |
| `GET` | `/api/v1/data/products` | Query clean products |
| `GET` | `/api/v1/data/quality-errors` | Failed records with raw payloads |

### Person 2 — Analytics & KPIs

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/analytics/overview` | Headline KPIs (revenue, AOV, orders, churn) |
| `GET` | `/api/v1/analytics/revenue-summary` | Total orders, revenue, AOV |
| `GET` | `/api/v1/analytics/sales-by-date` | Daily sales trend |
| `GET` | `/api/v1/analytics/sales-by-product` | Revenue & units per product |
| `GET` | `/api/v1/analytics/customer-frequency` | Order count & LTV per customer |
| `GET` | `/api/v1/analytics/ai-context` | Full analytics context snapshot for AI Agent |

### Person 3 — AI Business Intelligence Agent

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/agent/query` | Natural language Q&A about your business data |
| `POST` | `/api/v1/agent/recommendations` | Strategic action plan (5 prioritized recommendations) |
| `POST` | `/api/v1/agent/diagnose` | Root-cause anomaly diagnosis |
| `POST` | `/api/v1/agent/sql` | Safe SQL sandbox (read-only, whitelisted tables) |
| `GET` | `/api/v1/agent/suggestions` | Context-aware prompt suggestions |
| `GET` | `/api/v1/agent/capabilities` | Schema metadata & guardrail info |

---

## 🧠 Person 3 — AI Agent Features

### Natural Language Query Examples
```
"What was my revenue last month?"
"Which products are selling the best?"
"How many customers churned this week?"
"Show me the top 5 customers by lifetime value"
"Why did my cancellation rate spike?"
```

### SQL Safety Sandbox
- ✅ Allows: `SELECT`, `WITH`, `EXPLAIN` on 8 whitelisted tables
- ❌ Blocks: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, multi-statement injection, system catalog access

### Anomaly Diagnosis
Detects revenue drops, cancellation spikes, and churn risk with root-cause analysis and mitigation steps.

### Strategic Recommendations
5 prioritized business actions: AOV bundling, win-back campaigns, inventory optimization, cancellation reduction, category expansion.

### LLM Integration (Optional)
Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env` to enable AI-synthesized narrative responses. Falls back gracefully to deterministic engine when no key is set.

---

## 🖥️ Frontend Dashboard

Built with **React 19 + TypeScript + Vite + Tailwind CSS**.

- 📊 **KPI Cards** — Revenue, orders, AOV, churn rate at a glance
- 📈 **Revenue Charts** — Daily trends, product performance breakdowns
- 🤖 **AI Copilot Modal** (5 tabs):
  - **Chat** — NL Q&A with quick prompt pills and follow-up suggestions
  - **Action Plan** — Lazy-loaded strategic recommendations with checklists
  - **Anomaly Diagnosis** — Severity-badged root causes and mitigations
  - **SQL Runner** — Write and execute safe SELECT queries interactively
  - **Raw Context** — Full analytics JSON snapshot from Person 2

## 🔌 Live Integrations

The backend supports read-only HubSpot and Stripe connectors in addition to CSV uploads and the synthetic mock e-commerce API. Add `HUBSPOT_ACCESS_TOKEN` and/or `STRIPE_SECRET_KEY` to `ai-bi-agent/.env`, restart the backend, then register the source and sync it from the dashboard. HubSpot contacts map to customers; Stripe PaymentIntents map to completed, canceled, or refunded orders. CRM deals are not counted as sales, and Stripe currency conversion is not implemented.

---

## 🧪 Test Suite

**112 tests passing** across unit and integration levels:

```bash
cd ai-bi-agent
pytest -v
```

| Test File | Tests | Description |
|---|---|---|
| `tests/unit/test_cleaner.py` | 26 | Data cleaning & normalization |
| `tests/unit/test_deduplication.py` | 5 | Duplicate detection logic |
| `tests/unit/test_validator.py` | 13 | Field validation rules |
| `tests/unit/test_analytics_service.py` | 21 | KPI computation |
| `tests/unit/test_ai_agent_service.py` | 21 | AI Agent + SQL safety |
| `tests/unit/test_platform_connectors.py` | 3 | HubSpot and Stripe connector mapping |
| `tests/integration/test_ingestion_workflow.py` | 10 | End-to-end ETL pipeline |
| `tests/integration/test_api_endpoints.py` | 7 | Person 1 API endpoints |
| `tests/integration/test_analytics_api.py` | 6 | Person 2 analytics API |

---

## 🎬 Demo Scripts

```bash
cd ai-bi-agent

# Person 1: Verify ETL pipeline with dirty data
python scripts/verify_demo.py

# Person 3: 7-step AI Agent demonstration
python scripts/demo_ai_agent.py

# Seed analytics demo data
python scripts/seed_demo_analytics.py
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql://bi_user:bi_password@localhost:5432/bi_db

# Mock API
MOCK_API_BASE_URL=http://localhost:8001

# Optional live integrations
HUBSPOT_ACCESS_TOKEN=
STRIPE_SECRET_KEY=

# Person 3 — AI Agent (optional, enables LLM synthesis)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
AI_AGENT_MODEL=gemini-2.0-flash
AI_AGENT_TEMPERATURE=0.3
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI + Pydantic + SQLAlchemy 2.0 |
| **Database** | PostgreSQL 16 (SQLite for local/test) |
| **Data Processing** | Pandas + NumPy |
| **Scheduler** | APScheduler |
| **Frontend** | React 19 + TypeScript + Vite + Tailwind CSS |
| **Charts** | Recharts |
| **AI / LLM** | Google Gemini / OpenAI (optional) |
| **Containerization** | Docker + Docker Compose |
| **Testing** | pytest + FastAPI TestClient |
