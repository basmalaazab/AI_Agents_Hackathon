"""
Person 3: AI Business Intelligence Agent — Interactive Demonstration Runner.

Demonstrates:
1. Schema introspection & safety guardrail verification.
2. Natural language business intelligence query execution.
3. Safe read-only text-to-SQL querying & data formatting.
4. Security guardrail enforcement against unsafe SQL mutation attempts.
5. Root-cause anomaly diagnosis on live business metrics.
6. Strategic actionable recommendations generation with prioritized action steps.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

# Windows UTF-8 stdout fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Configure environment for standalone demo execution

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///bi_db.sqlite"

# SQLite JSONB patch for standalone run
from sqlalchemy import JSON
import sqlalchemy.dialects.postgresql as pg_dialect
class _SQLiteCompatibleJSON(JSON):
    pass
pg_dialect.JSONB = _SQLiteCompatibleJSON  # type: ignore

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, engine, SessionLocal
from app.services.ai_agent_service import AIAgentService, SQLSafetyValidator
from scripts.seed_demo_analytics import seed_rich_analytics_data


def run_agent_demo():
    print("=" * 65)
    print("   AI BUSINESS INTELLIGENCE AGENT — PERSON 3 DEMONSTRATION")
    print("=" * 65)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # Ensure demo database has rich records
    db = SessionLocal()
    order_count = 0
    try:
        order_count = db.execute(__import__("sqlalchemy").text("SELECT COUNT(*) FROM orders")).scalar() or 0
    except Exception:
        pass

    if order_count < 10:
        print("[*] Seeding demo database with rich business transactions...")
        db.close()
        seed_rich_analytics_data()
        db = SessionLocal()


    agent_svc = AIAgentService(db)

    # -----------------------------------------------------------------------
    # Step 1: Schema Introspection & Guardrails
    # -----------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("1. SCHEMA INTROSPECTION & SECURITY GUARDRAILS")
    print("-" * 65)
    meta = agent_svc.get_schema_metadata()
    print(f"[*] Exposed Clean Tables: {list(meta['tables'].keys())}")
    print(f"[*] Read-Only Enforcement: {meta['guardrails']['read_only']}")
    print(f"[*] Prohibited Keywords: {', '.join(meta['guardrails']['disallowed_keywords'])}")

    # -----------------------------------------------------------------------
    # Step 2: Natural Language Query — Revenue Overview
    # -----------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("2. NATURAL LANGUAGE Q&A: REVENUE & SALES INQUIRY")
    print("-" * 65)
    q1 = "What is our total revenue this month and how does it compare to the prior period?"
    print(f"[User Prompt] \"{q1}\"")
    r1 = agent_svc.process_query(q1, date_range="30d")
    print(f"[Intent Detected] {r1['intent']} (Model: {r1['model_used']})")
    print(f"\n{r1['answer']}")
    print(f"[Suggested Follow-ups]:")
    for f in r1['suggested_followups']:
        print(f"  -> {f}")

    # -----------------------------------------------------------------------
    # Step 3: Natural Language Query — Product Analysis
    # -----------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("3. NATURAL LANGUAGE Q&A: BEST SELLING PRODUCTS")
    print("-" * 65)
    q2 = "Which products are driving the most revenue?"
    print(f"[User Prompt] \"{q2}\"")
    r2 = agent_svc.process_query(q2, date_range="30d")
    print(f"[Intent Detected] {r2['intent']}")
    print(f"\n{r2['answer']}")

    # -----------------------------------------------------------------------
    # Step 4: Safe Read-Only SQL Execution Sandbox
    # -----------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("4. SAFE READ-ONLY TEXT-TO-SQL EXECUTION")
    print("-" * 65)
    safe_sql = (
        "SELECT oi.product_name, SUM(oi.quantity) AS total_units, "
        "SUM(oi.line_total) AS total_sales_usd "
        "FROM order_items oi JOIN orders o ON o.id = oi.order_id "
        "WHERE o.status = 'completed' "
        "GROUP BY oi.product_name ORDER BY total_sales_usd DESC LIMIT 3"
    )
    print(f"[SQL Query]:\n{safe_sql}\n")
    sql_res = agent_svc.execute_safe_sql(safe_sql)
    if sql_res["success"]:
        print(f"[Result Status] Success ({sql_res['row_count']} rows returned):")
        for idx, row in enumerate(sql_res["rows"], 1):
            print(f"  {idx}. {row['product_name']} | Units: {row['total_units']} | Revenue: ${row['total_sales_usd']:,.2f}")
    else:
        print(f"[Result Status] Error: {sql_res.get('error')}")

    # -----------------------------------------------------------------------
    # Step 5: SQL Safety Guardrail Enforcement (Blocking Dangerous Operations)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("5. SECURITY GUARDRAILS: BLOCKING UNAUTHORIZED SQL MUTATIONS")
    print("-" * 65)
    malicious_queries = [
        "DROP TABLE customers;",
        "DELETE FROM orders WHERE total_amount > 0;",
        "SELECT * FROM orders; DROP TABLE products;",
        "SELECT * FROM admin_passwords;",
    ]
    for m_sql in malicious_queries:
        is_safe, reason = SQLSafetyValidator.validate(m_sql)
        status_badge = "BLOCKED" if not is_safe else "ALLOWED"
        print(f"[{status_badge}] Query: {m_sql}")
        print(f"          Reason: {reason}")

    # -----------------------------------------------------------------------
    # Step 6: Anomaly Diagnosis & Root Cause Analysis
    # -----------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("6. ROOT-CAUSE ANOMALY DIAGNOSIS")
    print("-" * 65)
    diagnoses = agent_svc.diagnose_anomalies(date_range="30d")
    print(f"[*] Diagnosed Anomalies Detected: {len(diagnoses)}")
    for d in diagnoses:
        print(f"\n[{d['severity'].upper()}] {d['title']}")
        print(f"Summary: {d['summary']}")
        print("Root Causes:")
        for rc in d["root_causes"]:
            print(f"  - {rc}")
        print("Mitigation Steps:")
        for act in d["mitigation_actions"][:2]:
            print(f"  * {act}")

    # -----------------------------------------------------------------------
    # Step 7: Strategic Actionable Recommendations
    # -----------------------------------------------------------------------
    print("\n" + "-" * 65)
    print("7. STRATEGIC PRIORITIZED BUSINESS RECOMMENDATIONS")
    print("-" * 65)
    recs = agent_svc.generate_recommendations(date_range="30d")
    print(f"[*] Executive Summary: {recs['executive_summary']}")
    print(f"[*] High Priority Actions: {recs['high_priority_count']} of {recs['total_recommendations']}")
    for r in recs["recommendations"][:2]:
        print(f"\n[{r['priority']}] {r['title']}")
        print(f"Category: {r['category']} | Impact: {r['expected_impact']} | Effort: {r['implementation_effort']}")
        print(f"Data Justification: {r['data_justification']}")
        print("Action Checklist:")
        for step in r["action_steps"]:
            print(f"  [ ] {step}")

    db.close()
    print("\n" + "=" * 65)
    print("   PERSON 3 AI AGENT VERIFICATION RUN COMPLETED SUCCESSFULLY")
    print("=" * 65)


if __name__ == "__main__":
    run_agent_demo()
