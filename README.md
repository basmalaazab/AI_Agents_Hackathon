# 📊 Clearview BI — Digital Business Intelligence & AI Analyst

> **Production-grade Digital Business Intelligence Solution designed for small business owners and startups.**  
> Transform operational data from multiple sources (Stripe, HubSpot, Shopify, POS, CSV) into reliable business decisions, actionable growth plans, and natural-language AI insights in English and Arabic.

---

## 🌟 Key Highlights

- **Executive AI Business Analyst:** Centered right on the workspace overview. Ask questions in natural English or Arabic and get answers backed by factual database records with separated facts and recommendations.
- **Centralized Data Ingestion:** Connect external platforms (Stripe payments, HubSpot CRM, Shopify, POS terminals) and upload CSV files with automated deduplication and schema validation.
- **Real-Time KPIs & Trends:** Executive dashboard displaying Revenue, Order Volume, Average Order Value (AOV), Repeat Customer Rate, and Product/Customer performance.
- **Root-Cause Anomaly Diagnostics:** Deterministic diagnostics that identify revenue drops, high cancellation spikes, and dormant customer cohorts.
- **Safe Read-Only SQL Inspection:** Integrated read-only SQL execution environment secured with keyword and table whitelisting guardrails.
- **Multilingual Support:** Fully responsive bilingual AI reasoning capable of understanding and answering in fluent Arabic or professional English.

---

## 🏛️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                    │
│   CSV Imports │ Stripe Payments │ HubSpot CRM │ POS Terminals │ E-Commerce   │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         INGESTION & ETL PIPELINE                             │
│  Validate → Sanitize → Deduplicate → Load                                    │
│  • Raw audit trail preserved in raw_records                                  │
│  • Data quality errors tracked in data_quality_errors                        │
│  • Normalized tables: customers, orders, order_items, products               │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
┌───────────────────────────┐  ┌────────────────────────────────────────────┐
│     ANALYTICS ENGINE      │  │           AI ANALYST ENGINE                │
│  • Overview KPIs          │  │  • Natural Language Query Processing       │
│  • Revenue & Sales Trends │  │  • Bilingual Arabic & English Reasoning    │
│  • AOV & Customer Health  │  │  • Deterministic Analytical Engine         │
│  • Dynamic Alert Rules    │  │  • Root-Cause Anomaly Diagnostics          │
│  • CSV Analytics Export   │  │  • Strategic Action Plans                  │
└───────────┬───────────────┘  │  • Optional LLM Synthesis (Gemini/OpenAI)  │
            │                  └──────────────────┬─────────────────────────┘
            │                                     │
            └──────────────┬──────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                 CLEARVIEW BI — MODERN REACT WORKSPACE                        │
│  Workspace Navigation: Overview │ AI Analyst │ Data Sources │ Activity       │
│  Executive Green Design System │ Accessible │ Dark/Light Modes │ Mobile 390px │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Docker Compose

```bash
cd ai-bi-agent
cp .env.example .env          # Set environment configuration
docker compose up --build
```

| Service | Address |
|---|---|
| Frontend Workspace | http://localhost:5173 |
| FastAPI Backend API | http://localhost:8000 |
| Interactive API Docs | http://localhost:8000/docs |
| System Health Check | http://localhost:8000/api/v1/health |

---

### Option 2: Local Development

#### 1. Backend Setup (FastAPI & SQLite / PostgreSQL)

```bash
cd ai-bi-agent

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate           # On Windows
# source .venv/bin/activate      # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Launch FastAPI backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup (React + TypeScript + Vite)

```bash
cd ai-bi-agent/frontend

# Install node dependencies
npm install

# Start development server
npm run dev
```

Visit **http://localhost:5173** to access the application.

---

## 🔒 Security & Data Integrity

- **Strict Read-Only SQL:** Queries processed by the AI Analyst must begin with `SELECT` or `WITH`. Prohibited keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`) are blocked before database execution.
- **Server-Side Credentials:** API keys and credentials for third-party platforms are stored strictly on the backend environment—never exposed to or stored in client browsers.
- **Accurate State Reporting:** Real status checks via `/api/v1/health`. Indicators reflect verifiable database and connector states rather than simulated metrics.

---

## 🛠️ Testing & Verification

```bash
# Frontend build & lint
cd ai-bi-agent/frontend
npm run lint
npm run build

# Backend unit & integration tests
cd ai-bi-agent
pytest tests/unit/ tests/integration/ -v
```

---

## 📄 License

Internal proprietary release for small business analytics management.
