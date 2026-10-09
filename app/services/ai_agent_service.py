"""
AI Agent Service — Person 3 (AI Business Intelligence Agent).

Provides:
1. SQL Safety Guardrails (safe, read-only text-to-SQL validation).
2. Database Schema Introspection and Metadata.
3. Natural Language Business Intelligence & Q&A.
4. Anomaly Diagnosis & Root Cause Analysis.
5. Strategic Actionable Recommendations Engine.
6. Contextual Prompt Suggestions & Conversation Context.
7. Multi-Provider LLM Integration (OpenAI / Gemini) with 100% resilient Built-in Analytic Reasoning Fallback.
"""
from datetime import datetime, timezone
from decimal import Decimal
import logging
import math
import os
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.data_source import DataSource
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SQL Safety Guardrails
# ---------------------------------------------------------------------------

class SQLSafetyValidator:
    """
    Validates that SQL queries are strictly read-only and operate exclusively
    on whitelisted analytical and operational business tables.
    """

    ALLOWED_TABLES: Set[str] = {
        "customers",
        "orders",
        "order_items",
        "products",
        "data_sources",
        "ingestion_runs",
        "raw_records",
        "data_quality_errors",
    }

    # Prohibited SQL write, DDL, administration, or dangerous execution keywords
    DISALLOWED_KEYWORDS: List[str] = [
        r"\bDROP\b",
        r"\bDELETE\b",
        r"\bUPDATE\b",
        r"\bINSERT\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bREPLACE\b",
        r"\bEXEC\b",
        r"\bEXECUTE\b",
        r"\bCREATE\b",
        r"\bMERGE\b",
        r"\bUPSERT\b",
        r"\bCALL\b",
        r"\bCOPY\b",
        r"\bATTACH\b",
        r"\bDETACH\b",
        r"\bPRAGMA\b",
        r"\bVACUUM\b",
        r"\bREINDEX\b",
        r"\bINTO\b\s+(?:OUTFILE|DUMPFILE)",
    ]

    # Prohibited system catalog tables/schemas to avoid leaking internals
    RESTRICTED_SCHEMAS: List[str] = [
        r"\binformation_schema\b",
        r"\bpg_catalog\b",
        r"\bpg_tables\b",
        r"\bpg_stat\b",
        r"\bsqlite_master\b",
        r"\bsqlite_schema\b",
        r"\bsqlite_temp_master\b",
    ]

    @classmethod
    def validate(cls, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validates SQL string for safety.
        Returns:
            (True, None) if safe.
            (False, "Reason") if disallowed.
        """
        if not query or not query.strip():
            return False, "Query cannot be empty."

        clean = query.strip()

        # Remove SQL line and block comments before checking
        clean = re.sub(r"--.*$", "", clean, flags=re.MULTILINE)
        clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL).strip()

        if not clean:
            return False, "Query contains only comments."

        # Verify query starts with an approved read-only keyword (SELECT, WITH, EXPLAIN)
        first_word = clean.split()[0].upper()
        if first_word not in {"SELECT", "WITH", "EXPLAIN"}:
            return False, f"Prohibited operation: queries must begin with SELECT, WITH, or EXPLAIN (found '{first_word}')."

        # Check for multiple queries (semicolon followed by non-whitespace)
        statements = [s.strip() for s in clean.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multi-statement queries (separated by semicolons) are prohibited for safety."

        query_to_check = statements[0]

        # Check for disallowed modification keywords
        for pattern in cls.DISALLOWED_KEYWORDS:
            if re.search(pattern, query_to_check, re.IGNORECASE):
                return False, f"Prohibited SQL keyword detected matching security rule: {pattern}"

        # Check for restricted system tables
        for pattern in cls.RESTRICTED_SCHEMAS:
            if re.search(pattern, query_to_check, re.IGNORECASE):
                return False, "Access to internal database catalog schemas is restricted."

        # Check table references — ensure query references only allowed tables
        # Find all words that follow FROM or JOIN
        from_join_matches = re.findall(
            r"\b(?:FROM|JOIN)\s+([a-zA-Z0-9_\.\"]+)",
            query_to_check,
            re.IGNORECASE,
        )
        for match in from_join_matches:
            tbl = match.strip('"`').split(".")[-1].lower()
            # If it's a subquery or CTE alias, it might not be in ALLOWED_TABLES directly,
            # but any real physical table queried must be whitelisted
            if tbl not in cls.ALLOWED_TABLES:
                # Check if it was defined in a WITH clause CTE
                cte_match = re.search(rf"\bWITH\s+{tbl}\s+AS|\b,\s*{tbl}\s+AS", query_to_check, re.IGNORECASE)
                if not cte_match and tbl not in cls.ALLOWED_TABLES:
                    return False, f"Table '{tbl}' is not in the allowed business tables whitelist."

        return True, None

    @classmethod
    def sanitize_and_limit(cls, query: str, max_rows: int = 50) -> str:
        """Strips trailing semicolons and guarantees a LIMIT clause."""
        clean = query.strip().rstrip(";")
        # Check if LIMIT already present
        if not re.search(r"\bLIMIT\s+\d+", clean, re.IGNORECASE):
            clean = f"{clean} LIMIT {max_rows}"
        return clean


# ---------------------------------------------------------------------------
# Person 3 AI Agent Core Service
# ---------------------------------------------------------------------------

class AIAgentService:
    """
    AI Business Intelligence Agent providing:
    - Safe, structured read-only access to business data
    - Natural language query answering and metric interpretation
    - Root-cause anomaly diagnosis
    - Strategic prioritized business recommendations
    - Follow-up query generation
    """

    def __init__(self, db: Session):
        self.db = db
        self.analytics_svc = AnalyticsService(db)
        self.settings = get_settings()

    # -----------------------------------------------------------------------
    # Database Schema Introspection & Metadata
    # -----------------------------------------------------------------------

    def get_schema_metadata(self) -> Dict[str, Any]:
        """Returns structured metadata on all clean business tables."""
        return {
            "tables": {
                "customers": {
                    "description": "Clean customer directory with contact info and platform attribution.",
                    "primary_key": "id",
                    "columns": {
                        "id": "UUID (PK)",
                        "source_name": "VARCHAR(120) - Platform source name",
                        "external_id": "VARCHAR(255) - External platform customer ID",
                        "email": "VARCHAR(255) - Clean, lowercased email",
                        "first_name": "VARCHAR(120)",
                        "last_name": "VARCHAR(120)",
                        "city": "VARCHAR(120)",
                        "country": "VARCHAR(120)",
                        "created_at": "TIMESTAMPTZ (UTC)",
                    },
                    "relationships": ["Has many orders via orders.customer_id"],
                },
                "orders": {
                    "description": "Clean sales and order transactions with currency and status.",
                    "primary_key": "id",
                    "columns": {
                        "id": "UUID (PK)",
                        "source_name": "VARCHAR(120) - Platform source name",
                        "external_id": "VARCHAR(255) - External platform order ID",
                        "customer_id": "UUID (FK -> customers.id, nullable)",
                        "order_date": "TIMESTAMPTZ (UTC)",
                        "status": "VARCHAR(50) - 'completed', 'pending', 'cancelled', 'refunded'",
                        "total_amount": "NUMERIC(12,2)",
                        "currency": "CHAR(3) - ISO code (e.g. USD)",
                        "total_amount_usd": "NUMERIC(12,2) - Normalized USD value",
                    },
                    "relationships": [
                        "Belongs to customers via customer_id",
                        "Has many order_items via order_items.order_id",
                    ],
                },
                "order_items": {
                    "description": "Line items belonging to completed or pending orders.",
                    "primary_key": "id",
                    "columns": {
                        "id": "UUID (PK)",
                        "order_id": "UUID (FK -> orders.id)",
                        "product_id": "UUID (FK -> products.id, nullable)",
                        "product_name": "VARCHAR(255)",
                        "sku": "VARCHAR(120)",
                        "quantity": "INTEGER",
                        "unit_price": "NUMERIC(12,2)",
                        "line_total": "NUMERIC(12,2)",
                        "currency": "CHAR(3)",
                    },
                },
                "products": {
                    "description": "Product catalog with categories and standard unit prices.",
                    "primary_key": "id",
                    "columns": {
                        "id": "UUID (PK)",
                        "source_name": "VARCHAR(120)",
                        "external_id": "VARCHAR(255)",
                        "name": "VARCHAR(255)",
                        "sku": "VARCHAR(120)",
                        "category": "VARCHAR(120)",
                        "unit_price": "NUMERIC(12,2)",
                        "currency": "CHAR(3)",
                    },
                },
                "data_quality_errors": {
                    "description": "Audit log of dirty or invalid records rejected during ingestion.",
                    "columns": {
                        "id": "UUID (PK)",
                        "source_name": "VARCHAR(120)",
                        "record_type": "VARCHAR(50) - 'customer', 'order', 'product'",
                        "error_type": "VARCHAR(80) - e.g. 'missing_required_field', 'invalid_email'",
                        "error_message": "TEXT",
                        "created_at": "TIMESTAMPTZ (UTC)",
                    },
                },
            },
            "guardrails": {
                "read_only": True,
                "allowed_statements": ["SELECT", "WITH", "EXPLAIN"],
                "max_rows_default": 50,
                "disallowed_keywords": ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"],
            },
        }

    # -----------------------------------------------------------------------
    # Safe SQL Execution
    # -----------------------------------------------------------------------

    def execute_safe_sql(self, query_str: str, max_rows: int = 50) -> Dict[str, Any]:
        """
        Validates and executes a read-only SQL query safely against the database.
        Returns columns, row dictionaries, row count, and execution metadata.
        """
        if "workspace_id" in self.db.info:
            return {"success": False, "error": "SQL evidence is unavailable in company workspaces; use scoped analytics results.",
                    "query": query_str, "columns": [], "rows": [], "row_count": 0}
        is_safe, error_msg = SQLSafetyValidator.validate(query_str)
        if not is_safe:
            return {
                "success": False,
                "error": error_msg,
                "query": query_str,
                "columns": [],
                "rows": [],
                "row_count": 0,
            }

        sanitized_query = SQLSafetyValidator.sanitize_and_limit(query_str, max_rows=max_rows)

        try:
            result = self.db.execute(text(sanitized_query))
            columns = list(result.keys()) if result.returns_rows else []
            raw_rows = result.fetchall() if result.returns_rows else []

            serializable_rows = []
            for r in raw_rows:
                row_dict = {}
                for idx, col in enumerate(columns):
                    val = r[idx]
                    if isinstance(val, (datetime,)):
                        row_dict[col] = val.isoformat()
                    elif isinstance(val, (UUID,)):
                        row_dict[col] = str(val)
                    elif isinstance(val, (Decimal,)):
                        row_dict[col] = float(val)
                    else:
                        row_dict[col] = val
                serializable_rows.append(row_dict)

            return {
                "success": True,
                "query": sanitized_query,
                "columns": columns,
                "rows": serializable_rows,
                "row_count": len(serializable_rows),
                "is_limited": len(serializable_rows) >= max_rows,
            }
        except Exception as exc:
            logger.error("Error executing safe SQL query '%s': %s", sanitized_query, exc)
            return {
                "success": False,
                "error": f"Database execution error: {str(exc)}",
                "query": sanitized_query,
                "columns": [],
                "rows": [],
                "row_count": 0,
            }

    def _scope_generated_sql(
        self,
        query: str,
        date_range: str,
        source_name: Optional[str],
        alias: str = "",
    ) -> str:
        """Keep generated SQL evidence aligned with the selected analytics filters."""
        start, end, _, _ = self.analytics_svc.resolve_date_range(date_range)
        prefix = f"{alias}." if alias else ""
        predicates = []
        if source_name:
            escaped_source = source_name.replace("'", "''")
            predicates.append(f"{prefix}source_name = '{escaped_source}'")
        dialect = self.db.bind.dialect.name if self.db.bind is not None else ""
        for operator, value in ((">=", start), ("<=", end)):
            if value is not None:
                if dialect == "sqlite":
                    value = value.astimezone(timezone.utc).replace(tzinfo=None)
                predicates.append(f"{prefix}order_date {operator} '{value.isoformat(sep=' ')}'")
        clean = query.rstrip().rstrip(";")
        if predicates:
            clause_match = re.search(r"\b(?:GROUP\s+BY|ORDER\s+BY|LIMIT)\b", clean, re.IGNORECASE)
            if clause_match:
                clean = (
                    clean[:clause_match.start()].rstrip()
                    + " AND " + " AND ".join(predicates) + " "
                    + clean[clause_match.start():]
                )
            else:
                clean += " AND " + " AND ".join(predicates)
        return clean + ";"

    def _get_aov_metric(self, kpis: Dict[str, Any]) -> Dict[str, Any]:
        """Safely retrieves the AOV metric dictionary regardless of key naming."""
        return kpis.get("avg_order_value") or kpis.get("average_order_value") or {
            "current": 0.0,
            "previous": 0.0,
            "percentage_change": None,
        }

    def _build_analysis_evidence(
        self,
        ai_context: Dict[str, Any],
        date_range: str,
        source_name: Optional[str],
        intent: str,
    ) -> Dict[str, Any]:
        """Return the exact workspace scope and sample limits behind an answer."""
        kpis = ai_context["headline_kpis"]
        breakdown = ai_context["sales_performance"]
        customer_health = ai_context["customer_health"]
        if "workspace_id" in self.db.info:
            source_names = sorted(self.db.info.get("workspace_source_names", ()))
            source_labels = self.db.info.get("workspace_source_labels", {})
        else:
            source_rows = self.db.query(DataSource.name, DataSource.display_name).order_by(DataSource.name.asc()).all()
            source_names = [row.name for row in source_rows]
            source_labels = {row.name: row.display_name or row.name for row in source_rows}
        source_exists = not source_name or source_name in source_names
        orders = int(kpis["orders"]["current"] or 0)
        attempts = int(kpis["cancellation_rate"].get("total_order_attempts") or 0)
        customers = int(customer_health.get("total_registered_customers") or 0)
        stocked = int(ai_context.get("inventory_risk", {}).get("products_with_stock_data") or 0)
        notes = []
        if not source_exists:
            level = "insufficient"
            notes.append("This source is not available in the company workspace, so a source-specific conclusion is not supported.")
        elif intent in {"customer_analysis", "retention_analysis", "winback_campaign"} and customers == 0:
            level = "insufficient"
            notes.append("No customer records are imported for this source; retention and churn cannot be assessed.")
        elif intent in {"product_analysis", "category_analysis"} and not breakdown.get("top_products"):
            level = "insufficient"
            notes.append("No product line items are recorded for this source and period.")
        elif intent == "inventory_risk" and stocked == 0:
            level = "insufficient"
            notes.append("Product stock quantities are missing, so stock risk cannot be calculated.")
        elif intent == "data_quality_audit":
            level = "insufficient"
            notes.append("Data-quality issue totals are not available through the current workspace-scoped analysis, so I cannot quantify them.")
        elif intent == "direct_sql":
            level = "insufficient"
            notes.append("Direct SQL is disabled for company workspaces; ask a supported business question instead.")
        elif orders == 0 and attempts == 0:
            level = "insufficient"
            notes.append("No order attempts are recorded for this source and period; sales performance cannot be assessed.")
        elif orders < 5:
            level = "limited"
            notes.append("This period has fewer than five completed orders; comparisons are directional and should not be treated as conclusive.")
        else:
            level = "sufficient"
            notes.append("Figures come from imported records. They describe observed results but do not by themselves prove why a change happened.")
        period = ai_context.get("selected_period", {})
        period_labels = {"today": "Today", "7d": "Last 7 days", "30d": "Last 30 days", "3m": "Last 3 months",
                         "6m": "Last 6 months", "12m": "Last 12 months", "all": "All time", "custom": "Custom period"}
        return {
            "period": {"label": period_labels.get(date_range, date_range),
                       "start": period.get("current_start"), "end": period.get("current_end")},
            "source_scope": [source_labels.get(source_name, source_name)] if source_name and source_exists else ([source_labels.get(name, name) for name in source_names] if source_exists else []),
            "source_scope_label": source_labels.get(source_name, source_name) if source_name and source_exists else ("No matching source" if not source_exists else "All company sources"),
            "sample": {"completed_orders": orders, "order_attempts": attempts,
                       "customer_records": customers, "products_with_sales": len(breakdown.get("top_products", [])),
                       "stocked_products": stocked},
            "sufficiency": {"level": level, "notes": notes},
        }

    # -----------------------------------------------------------------------
    # Anomaly Diagnosis & Root Cause Analysis
    # -----------------------------------------------------------------------

    def diagnose_anomalies(
        self,
        date_range: str = "30d",
        source_name: Optional[str] = None,
        alert_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs in-depth root-cause diagnosis on detected business anomalies.
        Examines:
        - Revenue declines vs period baselines
        - Order volume dips
        - Cancellation surges and product concentrations
        - Customer repeat rate stagnation and churn risks
        """
        ai_context = self.analytics_svc.get_ai_context(date_range, source_name)
        kpis = ai_context["headline_kpis"]
        alerts = ai_context["business_alerts"]
        breakdown = ai_context["sales_performance"]
        customer_health = ai_context["customer_health"]
        trends = ai_context["daily_trend_summary"]
        aov_metric = self._get_aov_metric(kpis)

        diagnoses: List[Dict[str, Any]] = []

        # 1. Revenue Drop Diagnosis
        rev_pct = kpis["revenue"]["percentage_change"]
        if rev_pct is not None and rev_pct < 0:
            root_causes = []
            contributing = []

            # Check if volume or AOV fell
            ord_pct = kpis["orders"]["percentage_change"]
            aov_pct = aov_metric.get("percentage_change")

            if ord_pct is not None and ord_pct < rev_pct:
                root_causes.append(
                    f"Order volume dropped sharply by {abs(ord_pct)}%, which is the primary driver of the revenue contraction."
                )
            elif aov_pct is not None and aov_pct < -5:
                root_causes.append(
                    f"Average Order Value dropped by {abs(aov_pct)}% (from ${aov_metric.get('previous', 0)} to ${aov_metric.get('current', 0)}), indicating customer basket sizes shrank."
                )


            # Check category contribution
            top_cats = breakdown.get("top_categories", [])
            if top_cats:
                lowest_cat = min(top_cats, key=lambda c: c.get("revenue", 0))
                contributing.append(f"Lowest performing active category: {lowest_cat.get('category')} (${lowest_cat.get('revenue', 0):,.2f})")

            # Check peak/lowest days
            if trends.get("lowest_revenue_day"):
                low_day = trends["lowest_revenue_day"]
                contributing.append(f"Trough day recorded on {low_day.get('date')} with only ${low_day.get('revenue', 0):,.2f} revenue.")

            diagnoses.append({
                "id": "diag_revenue_decline",
                "title": "Revenue Contraction Diagnosis",
                "severity": "danger" if rev_pct <= -20 else "warning",
                "metric": "revenue",
                "current_value": kpis["revenue"]["current"],
                "baseline_value": kpis["revenue"]["previous"],
                "change_pct": rev_pct,
                "summary": f"Revenue is down {abs(rev_pct)}% relative to the preceding comparison period.",
                "root_causes": root_causes or ["General decrease in transaction frequency across product catalog."],
                "contributing_factors": contributing,
                "evidence": {
                    "revenue_difference_usd": round(kpis["revenue"]["current"] - kpis["revenue"]["previous"], 2),
                    "orders_change_pct": ord_pct,
                    "aov_change_pct": aov_pct,
                },
                "mitigation_actions": [
                    "Launch re-engagement campaigns targeting repeat customers who purchased in the prior period.",
                    "Bundle top complementary items with slower moving categories to lift Average Order Value.",
                    "Implement time-limited promotional incentives on high-margin product lines.",
                ],
            })

        # 2. High Cancellation Rate Diagnosis
        canc = kpis.get("cancellation_rate", {})
        canc_rate = canc.get("current", 0.0)
        canc_orders = canc.get("cancelled_orders", 0)
        total_att = canc.get("total_order_attempts") or canc.get("total_orders_attempted") or canc.get("total_attempts", 0)
        if (
            kpis["orders"]["current"] == 0
            and total_att == 0
            and not breakdown.get("top_products")
            and customer_health.get("active_in_period", 0) == 0
        ):
            return [{
                "id": "diag_insufficient_data",
                "title": "Insufficient data for diagnosis",
                "severity": "info",
                "metric": "data_coverage",
                "current_value": 0,
                "baseline_value": None,
                "change_pct": None,
                "summary": "No orders or product sales are available for this source and period, so a business diagnosis cannot be supported.",
                "root_causes": [],
                "contributing_factors": [],
                "evidence": {"completed_orders": 0, "order_attempts": 0},
                "mitigation_actions": ["Import order and product sales records for the selected period, then run the diagnosis again."],
            }]
        if canc_rate >= 5.0:

            diagnoses.append({
                "id": "diag_high_cancellations",
                "title": "Order Cancellation & Refund Spike",
                "severity": "danger" if canc_rate >= 10.0 else "warning",
                "metric": "cancellation_rate",
                "current_value": canc_rate,
                "baseline_value": canc.get("previous", 0.0),
                "change_pct": canc.get("percentage_change"),
                "summary": f"Cancellation rate stands at {canc_rate}% ({canc_orders} orders lost).",
                "root_causes": [
                    "The available data confirms a high cancellation/refund rate but does not identify its cause. Payment failures, stock discrepancies, or shipping expectations are possibilities to investigate, not confirmed causes.",
                ],
                "contributing_factors": [
                    f"{canc_orders} out of {total_att} total order attempts failed or refunded.",
                    "Lost revenue cannot be quantified from cancellation counts alone; order values and refund details need review.",
                ],
                "evidence": {
                    "cancelled_orders_count": canc_orders,
                    "total_attempts": total_att,
                    "cancellation_rate_pct": canc_rate,
                },
                "mitigation_actions": [
                    "Verify payment gateway error codes for rejected transactions.",
                    "Audit inventory accuracy to prevent out-of-stock orders after purchase confirmation.",
                    "Implement automated follow-up emails immediately upon order cancellation offering assistance.",
                ],
            })


        # 3. Customer Churn & Retention Diagnosis
        repeat_rate = customer_health.get("repeat_customer_rate_pct", 0.0)
        at_risk = customer_health.get("churn_at_risk_count", 0)
        if repeat_rate < 30.0 or at_risk > 0:
            diagnoses.append({
                "id": "diag_customer_retention",
                "title": "Customer Retention & Churn Risk",
                "severity": "warning",
                "metric": "repeat_customer_rate",
                "current_value": repeat_rate,
                "baseline_value": None,
                "change_pct": None,
                "summary": f"Repeat customer rate is {repeat_rate}%, with {at_risk} existing customers at risk of churn.",
                "root_causes": [
                    "Purchase history can identify repeat-purchase patterns, but the available data does not explain why customers did not return.",
                ],
                "contributing_factors": [
                    f"{at_risk} customers meet the app's inactivity rule; this does not establish why they stopped purchasing.",
                    f"New customers acquired in period: {customer_health.get('new_in_period', 0)}.",
                ],
                "evidence": {
                    "repeat_rate_pct": repeat_rate,
                    "churn_risk_count": at_risk,
                    "active_customers": customer_health.get("active_in_period", 0),
                },
                "mitigation_actions": [
                    "Set up an automated win-back email sequence with a tailored discount code for at-risk accounts.",
                    "Create a customer VIP loyalty tier or store credit reward program for second orders.",
                ],
            })

        # Filter by alert_id if specified
        if alert_id:
            diagnoses = [d for d in diagnoses if alert_id in d["id"] or d.get("metric") in alert_id]

        # If no severe anomalies found, return positive health diagnosis
        if not diagnoses:
            diagnoses.append({
                "id": "diag_healthy_status",
                "title": "Business Performance Equilibrium",
                "severity": "info",
                "metric": "overall_health",
                "current_value": kpis["revenue"]["current"],
                "baseline_value": kpis["revenue"]["previous"],
                "change_pct": rev_pct,
                "summary": "No configured alert threshold was crossed in the available data. This does not establish that every business process is healthy.",
                "root_causes": [],
                "contributing_factors": [
                    f"Revenue: ${kpis['revenue']['current']:,.2f}",
                    f"Total completed orders: {kpis['orders']['current']}",
                    f"Cancellation rate: {canc_rate}%",
                ],
                "evidence": {"status": "normal"},
                "mitigation_actions": [
                    "Continue monitoring the measured revenue, order, and cancellation metrics.",
                    "Review operational metrics not represented in the imported data separately.",
                ],
            })

        evidence = self._build_analysis_evidence(ai_context, date_range, source_name, "anomaly_diagnosis")
        for diagnosis in diagnoses:
            diagnosis["analysis_evidence"] = evidence
        return diagnoses

    # -----------------------------------------------------------------------
    # Strategic Actionable Recommendations Engine
    # -----------------------------------------------------------------------

    def generate_recommendations(
        self,
        date_range: str = "30d",
        source_name: Optional[str] = None,
        category_focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates prioritized, concrete business recommendations backed by data.
        Categorized into:
        - Revenue & Growth
        - Customer Retention & Loyalty
        - Catalog & Merchandising
        - Operational Efficiency
        """
        ai_context = self.analytics_svc.get_ai_context(date_range, source_name)
        kpis = ai_context["headline_kpis"]
        breakdown = ai_context["sales_performance"]
        customer_health = ai_context["customer_health"]

        recommendations: List[Dict[str, Any]] = []

        rev_val = kpis["revenue"]["current"]
        aov_val = self._get_aov_metric(kpis)["current"]
        customer_count = customer_health.get("total_registered_customers", 0)
        repeat_rate = customer_health.get("repeat_customer_rate_pct", 0.0)

        at_risk = customer_health.get("churn_at_risk_count", 0)
        canc_rate = kpis["cancellation_rate"]["current"]
        top_prods = breakdown.get("top_products", [])
        top_cats = breakdown.get("top_categories", [])

        if not top_prods and not top_cats and customer_count == 0 and canc_rate == 0:
            return {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "period": ai_context["selected_period"],
                "total_recommendations": 0,
                "high_priority_count": 0,
                "executive_summary": "There is not enough order, product, or customer data for recommendations in this period and source.",
                "key_risks": [],
                "quick_wins": [],
                "recommendations": [],
                "analysis_evidence": self._build_analysis_evidence(ai_context, date_range, source_name, "recommendations"),
            }

        # Recommendation 1: AOV & Cross-Sell Bundling
        if aov_val > 0:
            top_prod_name = top_prods[0]["name"] if top_prods else "Best-selling items"
            recommendations.append({
                "id": "rec_boost_aov_bundling",
                "title": f"Test complementary bundles featuring '{top_prod_name}'",
                "category": "Revenue & Growth",
                "priority": "HIGH" if aov_val < 75.0 else "MEDIUM",
                "expected_impact": "Potential increase in average order value; measure with a small test",
                "implementation_effort": "LOW",
                "target_metric": "average_order_value",
                "data_justification": (
                    f"Current Average Order Value is ${aov_val:.2f}. "
                    f"Your top product '{top_prod_name}' generated "
                    f"${top_prods[0].get('revenue', 0):,.2f} across {top_prods[0].get('units_sold', 0)} units. "
                    if top_prods else f"Current Average Order Value is ${aov_val:.2f}. "
                ) + (
                    "A bundle test may increase basket size; compare results with the current average order value."
                ),
                "action_steps": [
                    f"Bundle '{top_prod_name}' with 1-2 complementary accessories at a 10% bundle discount.",
                    "Add an 'Often Bought Together' recommendation prompt on product checkout pages.",
                    f"Set a free shipping threshold 20% higher than your current AOV (suggested: ${round(aov_val * 1.25, 0)}).",
                ],
            })

        # Recommendation 2: Retention & Churn Win-Back Campaign
        if at_risk > 0 or (customer_count > 0 and repeat_rate < 35.0):
            recommendations.append({
                "id": "rec_winback_churn_campaign",
                "title": f"Deploy Automated Win-Back Sequence for {at_risk} At-Risk Customers",
                "category": "Customer Retention & Loyalty",
                "priority": "HIGH",
                "expected_impact": "Potential improvement in repeat purchases; measure campaign results",
                "implementation_effort": "LOW",
                "target_metric": "repeat_customer_rate",
                "data_justification": (
                    (
                        f"The observed repeat customer rate is {repeat_rate:.1f}%, with {at_risk} customers flagged as at risk "
                        "by the available purchase-history data."
                        if customer_count > 0 else
                        f"The available purchase history flags {at_risk} customers as at risk; a repeat-customer rate is unavailable because customer records are missing."
                    )
                ),
                "action_steps": [
                    "Segment the customer list by recency: filter customers with order_count >= 1 and last purchase > 30 days.",
                    "Send a personalized 3-part email campaign: Day 1 (We miss you), Day 4 (Exclusive 15% credit), Day 7 (Final reminder).",
                    "Offer personalized product recommendations based on their prior purchase history.",
                ],
            })

        # Recommendation 4: Cancellation Rate Mitigation
        if canc_rate >= 4.0:
            recommendations.append({
                "id": "rec_reduce_cancellations",
                "title": "Optimize Checkout & Payment Gateway to Reduce Order Drop-Off",
                "category": "Operational Efficiency",
                "priority": "HIGH",
                "expected_impact": "Potential reduction in cancelled or refunded orders; measure the rate after changes",
                "implementation_effort": "MEDIUM",
                "target_metric": "cancellation_rate",
                "data_justification": (
                    f"The observed cancellation / refund rate is {canc_rate:.1f}%. "
                    "The available data does not include payment failure codes or marketing spend, so review those systems to confirm the cause."
                ),
                "action_steps": [
                    "Inspect payment failure error codes to detect card declines or 3D-Secure drop-offs.",
                    "Clarify shipping timeframes and return policies clearly on product and cart pages.",
                    "Offer alternate checkout methods (e.g. PayPal, Apple Pay, Cash on Delivery).",
                ],
            })

        # Recommendation 5: Channel & Category Diversification
        if top_cats and len(top_cats) >= 2:
            leading_cat = top_cats[0]
            recommendations.append({
                "id": "rec_category_expansion",
                "title": f"Expand Assortment in Leading Category: '{leading_cat.get('category')}'",
                "category": "Catalog & Merchandising",
                "priority": "LOW",
                "expected_impact": "Potential category growth; validate with a small assortment test",
                "implementation_effort": "HIGH",
                "target_metric": "revenue",
                "data_justification": (
                    f"'{leading_cat.get('category')}' generates ${leading_cat.get('revenue', 0):,.2f} "
                    f"({leading_cat.get('percentage_of_total', 0)}% of category revenue in the selected period)."
                ),
                "action_steps": [
                    f"Analyze top customer reviews in '{leading_cat.get('category')}' to identify unmet feature requests.",
                    "Introduce 2 new variants or related SKUs within the same category.",
                ],
            })

        # Filter by category if requested
        if category_focus:
            recommendations = [r for r in recommendations if category_focus.lower() in r["category"].lower()]

        # Executive summary
        high_priority = [r for r in recommendations if r["priority"] == "HIGH"]
        priority_count_phrase = (
            f"{len(high_priority)} recommendation is"
            if len(high_priority) == 1
            else f"{len(high_priority)} recommendations are"
        )
        repeat_summary = f"{repeat_rate:.1f}% repeat customer rate" if customer_count else "repeat-customer rate unavailable (no customer records)"
        exec_summary = (
            f"Current period: ${rev_val:,.2f} revenue, {kpis['orders']['current']} orders, "
            f"{repeat_summary}, and {canc_rate:.1f}% cancellation / refund rate. "
            f"Generated {len(recommendations)} recommendations; {priority_count_phrase} marked high priority "
            "by the current rules. Treat these as ideas to test against your business data."
        )

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": ai_context["selected_period"],
            "total_recommendations": len(recommendations),
            "high_priority_count": len(high_priority),
            "executive_summary": exec_summary,
            "key_risks": [
                f"Customer churn risk: {at_risk} dormant customers",
                f"Cancellation rate at {canc_rate:.1f}%",
            ] if at_risk > 0 or canc_rate >= 5.0 else ["No critical business risks identified."],
            "quick_wins": [r["title"] for r in recommendations if r["implementation_effort"] == "LOW"][:3],
            "recommendations": recommendations,
            "analysis_evidence": self._build_analysis_evidence(ai_context, date_range, source_name, "recommendations"),
        }

    def prepare_inventory_reorder_draft(
        self,
        product_name: str,
        product_sku: Optional[str],
        source_name: str,
        supplier_lead_time_days: int,
        target_cover_days: int = 14,
    ) -> Dict[str, Any]:
        """Calculate a review-only restock draft from imported stock and sales facts."""
        inventory = self.analytics_svc.get_inventory_risk(source_name)
        product = next(
            (
                item for item in inventory.get("products", [])
                if item["name"] == product_name
                and (not product_sku or item.get("sku") == product_sku)
            ),
            None,
        )
        if product is None:
            return {"available": False, "message": "No stock record was found for this product and data source."}

        sold_30d = int(product["units_sold_last_30d"])
        stock = int(product["stock_quantity"])
        reorder_point = product.get("reorder_point")
        daily_sales = sold_30d / 30
        target_stock = None
        recommended_quantity = None
        basis = ""

        if sold_30d > 0:
            # Cover the supplier lead time plus the user-selected post-arrival buffer.
            velocity_target = math.ceil(daily_sales * (supplier_lead_time_days + target_cover_days))
            target_stock = max(velocity_target, int(reorder_point or 0))
            recommended_quantity = max(0, target_stock - stock)
            basis = (
                f"Based on {sold_30d} non-cancelled units sold in the last 30 days, "
                f"{supplier_lead_time_days} days supplier lead time, and {target_cover_days} days of extra cover."
            )
            if reorder_point is not None:
                basis += f" The target also respects the imported reorder point of {reorder_point} units."
        elif reorder_point is not None:
            target_stock = int(reorder_point)
            recommended_quantity = max(0, target_stock - stock)
            basis = (
                "No eligible sales were recorded in the last 30 days. This quantity only restores "
                "the imported reorder point; it is not a sales-velocity forecast."
            )
        else:
            return {
                "available": False,
                "product": product,
                "message": (
                    "There is not enough data to suggest a quantity: no eligible sales were recorded "
                    "in the last 30 days and no reorder point was imported."
                ),
            }

        return {
            "available": True,
            "status": "draft_for_review",
            "product": product,
            "supplier_lead_time_days": supplier_lead_time_days,
            "target_cover_days": target_cover_days,
            "average_daily_sales": round(daily_sales, 2),
            "target_stock_quantity": target_stock,
            "recommended_order_quantity": recommended_quantity,
            "basis": basis,
            "draft": {
                "title": f"Restock request: {product['name']}",
                "sku": product.get("sku"),
                "quantity": recommended_quantity,
                "status": "Pending human review and approval",
                "note": "Draft only. No supplier or purchasing system has been contacted.",
            },
        }

    # -----------------------------------------------------------------------
    # Natural Language Query & Reasoning Engine
    # -----------------------------------------------------------------------

    def process_query(
        self,
        query: str,
        date_range: str = "30d",
        source_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        include_sql: bool = True,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Processes a natural language business intelligence question.
        Returns:
        - Natural language response (Markdown)
        - Intent classification
        - Executed SQL and results (if relevant)
        - Key KPI summary
        - Follow-up suggestions
        - Diagnostics / recommendations (if triggered)
        """
        q_clean = query.strip()
        q_lower = q_clean.lower()
        is_arabic = bool(re.search(r"[\u0600-\u06FF]", q_clean))
        asks_why = any(
            term in q_lower
            for term in ("why", "cause", "reason", "what caused", "لماذا", "ليه", "سبب")
        )
        asks_about_products = any(
            term in q_lower
            for term in ("product", "products", "sku", "item", "منتج", "منتجات", "المنتجات", "السلع")
        )
        asks_for_recommendations = any(
            term in q_lower
            for term in (
                "recommend", "suggest", "strategy", "action plan", "what should", "how can we",
                "how to improve", "increase", "grow", "advice", "توصية", "توصيات", "اقتراح",
                "اقتراحات", "نصائح", "خطة", "لزيادة", "كيف أزيد", "كيف ازيد",
            )
        )

        # Gather baseline analytics context
        ai_context = self.analytics_svc.get_ai_context(date_range, source_name)
        kpis = ai_context["headline_kpis"]
        breakdown = ai_context["sales_performance"]
        customer_health = ai_context["customer_health"]
        trends = ai_context["daily_trend_summary"]

        executed_sql = None
        sql_results = None
        intent = "general_analysis"
        answer = ""
        followups = []

        # -------------------------------------------------------------------
        # Intent Classification & Built-in Analytical Reasoning
        # -------------------------------------------------------------------

        # 1. Direct SQL
        if q_lower.startswith("select") or q_lower.startswith("with "):
            intent = "direct_sql"
            sql_exec = self.execute_safe_sql(q_clean)
            executed_sql = sql_exec["query"]
            sql_results = sql_exec
            if sql_exec["success"]:
                answer = (
                    f"### \U0001f5c4\ufe0f SQL Query Execution Results\n\n"
                    f"**Executed Query:**\n```sql\n{sql_exec['query']}\n```\n\n"
                    f"**Returned Rows:** `{sql_exec['row_count']}` record(s).\n\n"
                )
                if sql_exec["rows"]:
                    headers = sql_exec["columns"]
                    answer += "| " + " | ".join(headers) + " |\n"
                    answer += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                    for row in sql_exec["rows"][:10]:
                        answer += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"
                    if sql_exec["row_count"] > 10:
                        answer += f"\n*... showing first 10 of {sql_exec['row_count']} rows.*"
            else:
                answer = f"\u26a0\ufe0f **SQL Execution Blocked / Failed:** {sql_exec.get('error')}"
            followups = [
                "Summarize these query results in plain English",
                "What recommendations follow from this data?",
            ]

        # Profit cannot be calculated from revenue and order data alone.
        elif not asks_for_recommendations and any(k in q_lower for k in [
            "profit", "profitability", "profit margin", "net income", "expenses", "cost of goods",
            "هامش الربح", "صافي الربح", "التكاليف", "المصروفات", "الربح", "ارباح", "أرباح",
        ]):
            intent = "unsupported_profit_analysis"
            answer = (
                "I can report revenue, but I can't calculate profit or profit margin because "
                "the connected data doesn't include product costs or business expenses. "
                "Add cost and expense data before using profit figures."
            )
            followups = [
                "What is our total revenue?",
                "Which products generate the most revenue?",
                "What is our average order value?",
            ]

        # Use imported inventory balances and sales velocity when available.
        elif any(k in q_lower for k in (
            "inventory", "stock", "out of stock", "stockout", "run out", "reorder",
            "on hand", "safety stock", "المخزون", "مخزون", "نفاد", "الكمية المتاحة",
        )):
            intent = "inventory_risk"
            inventory = ai_context.get("inventory_risk", {})
            inventory_products = inventory.get("products", [])
            top_products = breakdown.get("top_products", [])
            if inventory_products:
                top_one = next(
                    (p for p in inventory_products if top_products and p["name"] == top_products[0]["name"]),
                    inventory_products[0],
                )
                cover = top_one.get("estimated_days_of_cover")
                answer = (
                    f"The top product with stock data is **{top_one['name']}**: "
                    f"{top_one['stock_quantity']} units on hand and {top_one['units_sold_last_30d']} sold in the last 30 days. "
                    + (f"At that recent pace, estimated cover is **{cover} days**. " if cover is not None else "There were no recorded sales in the last 30 days, so days of cover cannot be estimated. ")
                    + ("This product is flagged as low stock. " if top_one["at_risk"] else "It is not currently flagged as low stock. ")
                    + "This is an estimate, not a guarantee: supplier lead time and safety-stock requirements are not included."
                )
                if any(term in q_lower for term in ("how many", "quantity", "reorder", "order more", "كمية", "أطلب", "اطلب", "إعادة الطلب")):
                    answer += (
                        " To estimate a reorder quantity, provide the supplier lead time and desired extra stock cover; "
                        "the Stock risk panel can prepare a draft for review."
                    )
            elif top_products:
                top_one = top_products[0]
                answer = (
                    f"The top product by revenue is **{top_one['name']}** with {top_one['units_sold']} units sold "
                    f"during `{date_range}`. I can't assess stockout risk yet because no current stock quantity "
                    "has been imported. Upload a product CSV with `stock_quantity` (and optionally `reorder_point`)."
                )
            else:
                answer = (
                    "I can't assess stockout risk because this period has no product sales data, "
                    "and no current product stock quantities have been imported."
                )
            followups = [
                "Which products are below their reorder point?",
                "How many days of stock cover does each product have?",
            ]

        # 2. Revenue & Sales
        elif not asks_why and not asks_about_products and not asks_for_recommendations and any(k in q_lower for k in [
            "revenue", "sales", "earnings", "turnover", "how much did we make",
            "total income", "gross", "profit", "how much money", "what did we make",
            "money", "income", "إيراد", "ايراد", "مبيعات", "ارباح", "أرباح", "دخل", "فلوس", "كم حققنا", "الأرباح", "الايرادات", "الإيرادات", "المبيعات",
        ]):
            intent = "revenue_analysis"
            rev  = kpis["revenue"]
            ordr = kpis["orders"]
            aov  = self._get_aov_metric(kpis)
            canc = kpis["cancellation_rate"]
            rev_change_str = (
                f"{rev['percentage_change']:+.1f}% vs previous period"
                if rev["percentage_change"] is not None else "No prior period data"
            )
            executed_sql = (
                "SELECT COUNT(*) AS total_orders, "
                "SUM(total_amount_usd) AS total_revenue_usd, "
                "AVG(total_amount_usd) AS avg_order_value_usd "
                "FROM orders WHERE status NOT IN ('cancelled', 'refunded');"
            )
            executed_sql = self._scope_generated_sql(executed_sql, date_range, source_name)
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            answer = (
                f"### \U0001f4b0 Revenue & Sales Performance\n\n"
                f"Period: `{date_range}`\n\n"
                f"- **Total Revenue:** `${rev['current']:,.2f}` ({rev_change_str})\n"
                f"- **Completed Orders:** `{ordr['current']}` orders\n"
                f"- **Average Order Value:** `${aov['current']:,.2f}`\n"
                f"- **Cancellation Rate:** `{canc['current']}%`\n\n"
            )
            if rev["percentage_change"] is not None and rev["percentage_change"] < 0:
                answer += (
                    f"\u26a0\ufe0f Revenue contracted by `{abs(rev['percentage_change'])}%` vs prior period. "
                    "Check root-cause diagnosis for details.\n\n"
                )
            elif rev["percentage_change"] is not None and rev["percentage_change"] > 0:
                answer += f"\U0001f680 Revenue grew by `{rev['percentage_change']}%` vs prior period!\n\n"
            followups = [
                "Why did revenue change vs last period?",
                "Which product generated the most revenue?",
                "How can we increase sales?",
            ]

        # 3. Average Order Value (AOV) - MUST come before general orders
        elif any(k in q_lower for k in [
            "aov", "average order", "average order value", "basket size",
            "average sale", "order average", "avg order", "average transaction",
            "متوسط الطلب", "قيمة الطلب", "متوسط السلة", "سلة المشتريات",
        ]):
            intent = "aov_analysis"
            aov  = self._get_aov_metric(kpis)
            rev  = kpis["revenue"]
            ordr = kpis["orders"]
            top_prods = breakdown.get("top_products", [])
            executed_sql = (
                "SELECT AVG(total_amount_usd) AS avg_order_value_usd, "
                "MIN(total_amount_usd) AS min_order, MAX(total_amount_usd) AS max_order "
                "FROM orders WHERE status NOT IN ('cancelled', 'refunded');"
            )
            executed_sql = self._scope_generated_sql(executed_sql, date_range, source_name)
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            aov_change = aov.get("percentage_change")
            aov_str = f"{aov_change:+.1f}% vs previous period" if aov_change is not None else "No prior data"
            answer = (
                f"### \U0001f6d2 Average Order Value (AOV)\n\n"
                f"- **AOV:** `${aov['current']:,.2f}` ({aov_str})\n"
                f"- **Total Revenue:** `${rev['current']:,.2f}` from `{ordr['current']}` orders\n\n"
            )
            answer += "AOV describes the observed order value; the available data does not determine whether that level is strong for your business.\n\n"
            if top_prods:
                answer += f"A bundle featuring **{top_prods[0]['name']}** is a testable idea; measure its effect against this AOV.\n"
            followups = [
                "What is our total revenue?",
                "How can we increase AOV?",
                "What are our top selling products?",
            ]

        # 4. Orders & Volume
        elif any(k in q_lower for k in [
            "how many orders", "order count", "number of orders", "order status",
            "volume", "transaction", "purchases", "completed orders",
            "pending", "fulfilled", "how many sales", "total orders", "orders",
            "order", "طلبات", "طلب", "عدد الطلبات", "طلبيات", "كم طلب", "المعاملات",
        ]):
            intent = "orders_analysis"
            ordr = kpis["orders"]
            canc = kpis["cancellation_rate"]
            rev  = kpis["revenue"]
            order_change_str = (
                f"{ordr['percentage_change']:+.1f}% vs previous period"
                if ordr.get("percentage_change") is not None else "No prior period data"
            )
            executed_sql = (
                "SELECT status, COUNT(*) AS count, SUM(total_amount_usd) AS total_usd "
                "FROM orders GROUP BY status ORDER BY count DESC;"
            )
            executed_sql = self._scope_generated_sql(executed_sql, date_range, source_name)
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            answer = (
                f"### \U0001f4e6 Orders & Volume Breakdown\n\n"
                f"- **Completed Orders:** `{ordr['current']}` ({order_change_str})\n"
                f"- **Revenue from Orders:** `${rev['current']:,.2f}`\n"
                f"- **Cancellation Rate:** `{canc['current']}%`\n\n"
            )
            if canc["current"] > 5.0:
                answer += (
                    f"\u26a0\ufe0f High cancellation rate `{canc['current']}%` — "
                    "above 5% healthy threshold.\n\n"
                )
            else:
                answer += "Cancellation rate is below this app's 5% alert threshold; that threshold is not a universal industry benchmark.\n\n"
            followups = [
                "Why is the cancellation rate high?",
                "Which products have the most orders?",
                "What is our average order value?",
            ]

        # 5. Products & Best Sellers
        elif any(k in q_lower for k in [
            "product", "best seller", "top seller", "sku", "item", "inventory",
            "best performing", "top product", "what sells", "most sold",
            "popular", "best product", "which product",
            "منتج", "منتجات", "الأكثر مبيعا", "الاكثر مبيعا", "أفضل منتج", "افضل منتج", "السلع", "السلعة", "المخزون",
        ]):
            intent = "product_analysis"
            top_prods = breakdown.get("top_products", [])
            executed_sql = (
                "SELECT oi.product_name, SUM(oi.quantity) AS units_sold, "
                "SUM(oi.line_total_usd) AS revenue_usd "
                "FROM order_items oi JOIN orders o ON o.id = oi.order_id "
                "WHERE o.status NOT IN ('cancelled', 'refunded') AND oi.line_total_usd IS NOT NULL "
                "GROUP BY oi.product_name ORDER BY revenue_usd DESC LIMIT 5;"
            )
            executed_sql = self._scope_generated_sql(executed_sql, date_range, source_name, alias="o")
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            answer = "### \U0001f3c6 Top Performing Products\n\n"
            if top_prods:
                answer += "| Product | Units Sold | Revenue |\n| --- | --- | --- |\n"
                for p in top_prods[:5]:
                    answer += f"| **{p['name']}** | {p['units_sold']} | ${p['revenue']:,.2f} |\n"
                top_one = top_prods[0]
                answer += (
                    f"\n\u2b50 **{top_one['name']}** is your #1 revenue driver "
                    f"with `${top_one['revenue']:,.2f}` across {top_one['units_sold']} units.\n"
                )
            else:
                answer += "No completed product sales recorded for this period.\n"
            followups = [
                "Which category performs best?",
                "How do we bundle top products to raise AOV?",
                "Is our top product at risk of running out of stock?",
            ]

        # 6. Customers & Retention
        elif any(k in q_lower for k in [
            "customer", "churn", "repeat", "loyalty", "ltv", "retention",
            "returning", "who are", "top customer", "best customer",
            "lifetime value", "how many customer", "at risk",
            "عميل", "عملاء", "ولاء", "زبائن", "زبون", "استبقاء", "خسارة العملاء", "الاحتفاظ",
        ]):
            intent = "customer_analysis"
            customer_count = customer_health.get("total_registered_customers", 0)
            rep_rate = customer_health.get("repeat_customer_rate_pct", 0.0)
            at_risk  = customer_health.get("churn_at_risk_count", 0)
            active   = customer_health.get("active_in_period", 0)
            new_cust = customer_health.get("new_in_period", 0)
            executed_sql = (
                "SELECT c.email, c.first_name, c.last_name, COUNT(o.id) AS order_count, "
                "SUM(o.total_amount_usd) AS lifetime_value_usd "
                "FROM customers c JOIN orders o ON o.customer_id = c.id "
                "WHERE o.status NOT IN ('cancelled', 'refunded') AND o.total_amount_usd IS NOT NULL "
                "GROUP BY c.id, c.email, c.first_name, c.last_name "
                "ORDER BY lifetime_value_usd DESC LIMIT 5;"
            )
            if source_name:
                escaped_source = source_name.replace("'", "''")
                executed_sql = executed_sql.replace(
                    "WHERE o.status NOT IN ('cancelled', 'refunded') AND o.total_amount_usd IS NOT NULL",
                    "WHERE o.status NOT IN ('cancelled', 'refunded') AND o.total_amount_usd IS NOT NULL "
                    f"AND c.source_name = '{escaped_source}' AND o.source_name = '{escaped_source}'",
                )
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            answer = (
                f"### \U0001f465 Customer Health & Retention\n\n"
                + (
                    f"- **Customer records:** `{customer_count}`\n"
                    f"- **Repeat Customer Rate:** `{rep_rate}%`\n"
                    f"- **Active Customers:** `{active}`\n"
                    f"- **New Customers Acquired:** `{new_cust}`\n"
                    f"- **Churn Risk:** `{at_risk}` customers\n\n"
                    if customer_count > 0 else
                    "No customer records are available for this source, so repeat rate, activity, and churn risk cannot be calculated.\n\n"
                )
            )
            if customer_count == 0:
                answer += "Import customer records linked to orders to enable retention analysis.\n\n"
            elif at_risk > 0:
                answer += (
                    f"\u26a0\ufe0f {at_risk} customers have lapsed beyond their repurchase interval. "
                    "Launch an automated win-back campaign.\n\n"
                )
            else:
                answer += "\u2705 Customer retention is currently stable.\n\n"
            followups = [
                "What win-back campaign should we send?",
                "Who are our top 5 most valuable customers?",
                "How do we increase the repeat customer rate?",
            ]

        # 7. Categories
        elif any(k in q_lower for k in [
            "category", "categories", "segment", "department", "product type",
            "collection", "breakdown by category",
            "فئة", "فئات", "تصنيف", "تصنيفات", "أقسام", "اقسام",
        ]):
            intent = "category_analysis"
            top_cats = breakdown.get("top_categories", [])
            executed_sql = (
                "SELECT p.category, COUNT(oi.id) AS units_sold, "
                "SUM(oi.line_total_usd) AS revenue_usd "
                "FROM order_items oi "
                "JOIN orders o ON o.id = oi.order_id "
                "JOIN products p ON p.id = oi.product_id "
                "WHERE o.status NOT IN ('cancelled', 'refunded') AND oi.line_total_usd IS NOT NULL "
                "GROUP BY p.category ORDER BY revenue_usd DESC;"
            )
            executed_sql = self._scope_generated_sql(executed_sql, date_range, source_name, alias="o")
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            answer = "### \U0001f4c2 Sales by Product Category\n\n"
            if top_cats:
                answer += "| Category | Units | Revenue |\n| --- | --- | --- |\n"
                for cat in top_cats[:6]:
                    answer += f"| **{cat.get('category', 'N/A')}** | {cat.get('units_sold', 0)} | ${cat.get('revenue', 0):,.2f} |\n"
                leading = top_cats[0]
                answer += f"\n\U0001f3c5 **{leading.get('category')}** leads with `${leading.get('revenue', 0):,.2f}`.\n"
            else:
                answer += "No category data available for this period.\n"
            followups = [
                "What product within the top category sells most?",
                "How should we expand the best category?",
                "What is our total revenue?",
            ]

        # 8. Anomaly & Root-Cause Diagnosis
        elif any(k in q_lower for k in [
            "why", "drop", "decline", "fall", "issue", "problem", "diagnos",
            "alert", "anomaly", "cancellation", "what went wrong", "explain",
            "cause", "reason", "spike", "sudden", "unexpected",
            "لماذا", "ليه", "انخفاض", "مشكلة", "سبب", "انخفضت", "انخفض", "قلت", "نزلت",
            "تراجعت", "تراجع", "خلل", "لما",
        ]):
            intent = "anomaly_diagnosis"
            diagnoses = self.diagnose_anomalies(date_range, source_name)
            answer = "### \U0001f52c Business Diagnosis\n\n"
            for d in diagnoses:
                badge = "\U0001f534" if d["severity"] == "danger" else ("\U0001f7e1" if d["severity"] == "warning" else "\U0001f535")
                answer += f"#### {badge} {d['title']}\n{d['summary']}\n\n"
                answer += "**Potential causes to verify:**\n"
                for rc in d["root_causes"]:
                    answer += f"- {rc}\n"
                answer += "\n**Actions:**\n"
                for act in d["mitigation_actions"]:
                    answer += f"- {act}\n"
                answer += "\n"
            followups = [
                "Generate full strategic action plan",
                "Show top products",
                "What is our AOV?",
            ]

        # 9. Win-back campaign guidance
        elif any(k in q_lower for k in [
            "win-back campaign", "win back campaign", "winback campaign", "reactivate customers",
            "re-engagement campaign", "حملة استرجاع", "حملة إعادة تنشيط", "حملة اعادة تنشيط",
        ]):
            intent = "winback_campaign"
            at_risk = customer_health.get("churn_at_risk_count", 0)
            customer_count = customer_health.get("total_registered_customers", 0)
            if customer_count == 0:
                answer = (
                    "### Win-back campaign audience\n\n"
                    "I can't identify an audience because no customer records are available for this source. "
                    "Import customers linked to orders before planning a customer-specific campaign. "
                    "This app does not send marketing messages."
                )
            elif at_risk > 0:
                answer = (
                    f"### Win-back campaign plan\n\n"
                    f"The available purchase history flags `{at_risk}` customers as inactive for over 60 days. "
                    "This app does not send marketing messages; use these steps in your email or CRM platform:\n\n"
                    "1. Review the inactive customer list and exclude unsubscribed contacts.\n"
                    "2. Send a helpful reminder tailored to the customer's last purchase.\n"
                    "3. Test an optional offer with a small group before sending it to everyone.\n"
                    "4. Measure returned purchases and revenue, and stop if the campaign does not help."
                )
            else:
                answer = (
                    "### Win-back campaign audience\n\n"
                    "No customers are currently flagged as inactive for over 60 days in the available data, "
                    "so the dashboard has no identified win-back audience for this period. "
                    "You can review purchase recency in your CRM and define a segment before launching a campaign. "
                    "This app does not send marketing messages."
                )
            followups = [
                "How many customers are flagged as inactive?",
                "What is our repeat customer rate?",
            ]

        # 10. Strategic Recommendations
        elif any(k in q_lower for k in [
            "recommend", "strategy", "action", "grow", "plan", "increase", "advice",
            "what should we do", "what should i do", "how to improve", "how can we",
            "suggestions", "tips", "next steps", "improve", "optimize",
            "توصيات", "توصية", "اقتراح", "اقتراحات", "خطة", "كيف أزيد", "كيف احسن", "نصائح", "استراتيجية", "ماذا أفعل", "ماذا افعل",
        ]):
            intent = "recommendations"
            recs_data = self.generate_recommendations(date_range, source_name)
            answer = f"### \U0001f4cb Strategic Action Plan\n\n{recs_data['executive_summary']}\n\n"
            for r in recs_data["recommendations"][:3]:
                p_badge = "\U0001f525 [HIGH]" if r["priority"] == "HIGH" else "\u26a1 [MEDIUM]"
                answer += f"#### {p_badge} {r['title']}\n"
                answer += f"**Impact:** `{r['expected_impact']}`\n\n_{r['data_justification']}_\n\n"
                answer += "**Steps:**\n"
                for step in r["action_steps"]:
                    answer += f"1. {step}\n"
                answer += "\n"
            followups = ["Diagnose why revenue changed", "Which products generate the most revenue?"]
            if any(r["id"] == "rec_winback_churn_campaign" for r in recs_data["recommendations"]):
                followups.insert(1, "How do we run the win-back campaign?")

        # 10. Trends & Daily Patterns
        elif any(k in q_lower for k in [
            "trend", "daily", "peak", "highest day", "lowest day", "calendar",
            "this week", "last week", "over time", "by date", "per day",
            "weekly", "monthly", "best day", "worst day", "when",
            "اتجاه", "يومي", "تاريخ", "الأيام", "الايام", "مخطط", "رسم بياني",
        ]):
            intent = "trend_analysis"
            peak       = trends.get("peak_revenue_day")
            low        = trends.get("lowest_revenue_day")
            total_days = trends.get("total_days_recorded", 0)
            executed_sql = (
                "SELECT DATE(order_date) AS sale_date, COUNT(*) AS orders, "
                "SUM(total_amount_usd) AS revenue_usd "
                "FROM orders WHERE status NOT IN ('cancelled', 'refunded') "
                "GROUP BY sale_date ORDER BY sale_date DESC LIMIT 7;"
            )
            executed_sql = self._scope_generated_sql(executed_sql, date_range, source_name)
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            answer = f"### \U0001f4c8 Daily Revenue Trends\n\nAcross `{total_days}` days:\n\n"
            if peak:
                answer += f"- \U0001f31f **Peak:** `{peak['date']}` — **${peak['revenue']:,.2f}** ({peak['orders']} orders)\n"
            if low:
                answer += f"- \U0001f4c9 **Lowest:** `{low['date']}` — **${low['revenue']:,.2f}** ({low['orders']} orders)\n"
            answer += "\nThese records show when revenue peaked or was lowest, but do not identify what caused the daily changes.\n"
            followups = [
                "What was our total revenue?",
                "Which products sold best on the peak day?",
                "How can we boost slow days?",
            ]

        # 11. Data Quality & Pipeline
        elif any(k in q_lower for k in [
            "quality", "pipeline", "ingest", "clean", "duplicate", "audit",
            "bad data", "invalid", "rejected", "missing", "data issue", "error",
            "جودة", "خطأ", "أخطاء", "بيانات مكررة", "مرفوضة",
        ]):
            intent = "data_quality_audit"
            executed_sql = (
                "SELECT record_type, error_type, COUNT(*) AS error_count "
                "FROM data_quality_errors GROUP BY record_type, error_type "
                "ORDER BY error_count DESC LIMIT 5;"
            )
            sql_results = self.execute_safe_sql(executed_sql)
            answer = "### \U0001f6e1\ufe0f Data Quality & Pipeline Audit\n\n"
            if sql_results["success"] and sql_results["rows"]:
                answer += "| Record Type | Error | Count |\n| --- | --- | --- |\n"
                for err in sql_results["rows"]:
                    answer += f"| `{err['record_type']}` | {err['error_type']} | **{err['error_count']}** |\n"
                answer += "\nThese are the quality errors recorded by the ingestion pipeline.\n"
            elif sql_results["success"]:
                answer += "No data-quality errors are recorded in the audit table. This does not validate records that were never ingested.\n"
            else:
                answer += "The quality audit could not be read, so I can't determine the number of rejected records.\n"
            followups = [
                "What are our clean order numbers?",
                "Show total revenue",
                "Inspect registered sources",
            ]

        # 12. Overview / Dashboard Summary
        elif any(k in q_lower for k in [
            "overview", "summary", "dashboard", "snapshot", "report",
            "how are we doing", "how is the business", "business health",
            "kpi", "metrics", "status", "ملخص", "نظرة عامة", "تقرير",
            "أداء الشركة", "كيف العمل", "الوضع المالي", "مؤشرات",
        ]):
            intent = "overview_summary"
            rev      = kpis["revenue"]["current"]
            orders_cnt = kpis["orders"]["current"]
            aov      = self._get_aov_metric(kpis)["current"]
            canc     = kpis["cancellation_rate"]["current"]
            rep_rate = customer_health.get("repeat_customer_rate_pct", 0.0)
            at_risk  = customer_health.get("churn_at_risk_count", 0)
            customer_count = customer_health.get("total_registered_customers", 0)
            top_prods = breakdown.get("top_products", [])
            answer = (
                f"### \U0001f4ca Business Overview — `{date_range}`\n\n"
                f"#### \U0001f4b0 Revenue\n"
                f"- Total: `${rev:,.2f}` | Orders: `{orders_cnt}` | AOV: `${aov:,.2f}` | Cancellations: `{canc}%`\n\n"
                f"#### \U0001f465 Customers\n"
                + (
                    f"- Customer records: `{customer_count}` | Repeat Rate: `{rep_rate}%` | Churn Risk: `{at_risk}`\n\n"
                    if customer_count else
                    "- Retention metrics unavailable: no customer records are linked to this source.\n\n"
                )
            )
            if top_prods:
                answer += f"#### \U0001f3c6 Top Product\n- **{top_prods[0]['name']}** — `${top_prods[0]['revenue']:,.2f}`\n\n"
            alerts = []
            if canc > 5.0:
                alerts.append(f"\U0001f534 Cancellation rate `{canc}%` above threshold")
            if at_risk > 0:
                alerts.append(f"\U0001f7e1 `{at_risk}` customers at churn risk")
            if customer_count > 0 and rep_rate < 30:
                alerts.append(f"\U0001f7e1 Low repeat rate `{rep_rate}%` — consider loyalty program")
            if alerts:
                answer += "#### \u26a0\ufe0f Alerts\n" + "\n".join(f"- {a}" for a in alerts)
            followups = [
                "Diagnose why metrics changed",
                "What are our top selling products?",
                "Give me a strategic action plan",
            ]

        # 13. Fallback
        else:
            intent = "general_query"
            answer = (
                f"### \U0001f916 AI Business Intelligence Agent\n\n"
                f"I couldn't match *\"{query}\"* to an analysis I support yet. "
                "I can answer questions about revenue, orders, products, customers, trends, "
                "data quality, and recommendations.\n\n"
                "Try asking:\n"
                "- *What is my total revenue?*\n"
                "- *Show me top selling products*\n"
                "- *How many orders do I have?*\n"
                "- *Why did revenue drop?*\n"
                "- *Give me 3 recommendations to grow*\n"
                "- *Who are my best customers?*\n"
                "- *What is my average order value?*\n"
                "- *Show me daily sales trends*\n"
            )
        # If Arabic query detected, generate response in clean, professional Arabic
        if is_arabic:
            ar_answer, ar_followups = self._generate_arabic_response(
                intent=intent,
                kpis=kpis,
                breakdown=breakdown,
                customer_health=customer_health,
                inventory_risk=ai_context.get("inventory_risk", {}),
                trends=trends,
                date_range=date_range,
                query=q_clean,
                source_name=source_name,
                executed_sql=executed_sql,
                sql_results=sql_results,
            )
            answer = ar_answer
            followups = ar_followups

        response_evidence = self._build_analysis_evidence(ai_context, date_range, source_name, intent)

        # -------------------------------------------------------------------
        # LLM Synthesis (if API key is configured)
        # -------------------------------------------------------------------
        model_used = "built-in-analyst"
        if intent not in {"direct_sql", "unsupported_profit_analysis"} and (
            self.settings.gemini_api_key or self.settings.openai_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        ):
            try:
                enhanced_answer, enhanced_model = self._synthesize_with_llm(
                    query=q_clean,
                    ai_context=ai_context,
                    draft_answer=answer,
                    conversation_history=conversation_history,
                    on_chunk=on_chunk,
                )
                if enhanced_answer:
                    answer = enhanced_answer
                    model_used = enhanced_model or "llm-augmented"
            except Exception as llm_exc:
                logger.warning("LLM synthesis failed, relying on deterministic reasoning: %s", llm_exc)

        if response_evidence["sufficiency"]["level"] != "sufficient":
            limitation = "; ".join(response_evidence["sufficiency"]["notes"])
            answer = f"### Data coverage\n\n**{response_evidence['sufficiency']['level'].title()}:** {limitation}\n\n{answer}"

        return {
            "query": q_clean,
            "intent": intent,
            "model_used": model_used,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "answer": answer,
            "executed_sql": executed_sql,
            "sql_results": sql_results,
            "metrics_snapshot": {
                "revenue": kpis["revenue"]["current"],
                "orders": kpis["orders"]["current"],
                "aov": self._get_aov_metric(kpis)["current"],
                "cancellation_rate": kpis["cancellation_rate"]["current"],
                "repeat_customer_rate": customer_health.get("repeat_customer_rate_pct") if customer_health.get("total_registered_customers", 0) else None,
                "churn_risk_count": customer_health.get("churn_at_risk_count") if customer_health.get("total_registered_customers", 0) else None,
            },
            "suggested_followups": followups,
            "analysis_evidence": response_evidence,
        }


    # -----------------------------------------------------------------------
    # LLM Synthesis Helper
    # -----------------------------------------------------------------------

    def _synthesize_with_llm(
        self,
        query: str,
        ai_context: Dict[str, Any],
        draft_answer: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Optionally enhances answer using OpenAI first, then Google Gemini fallback, or returns None."""
        openai_key = self.settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        gemini_key = self.settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")

        is_arabic = bool(re.search(r"[\u0600-\u06FF]", query))
        lang_instruction = (
            "اللغة: السؤال باللغة العربية. يجب أن تجيب بلغة عربية فصحى واضحة، احترافية ومرتبة باستخدام Markdown. حافظ على الأرقام والنسب والعملات كما هي في المسودة."
            if is_arabic
            else "Language: Respond in clear, professional English with clean markdown formatting and bold headers."
        )

        prompt = (
            f"You are the AI Business Intelligence Agent for a small business.\n"
            f"{lang_instruction}\n\n"
            f"Grounding Rules:\n"
            f"- Treat the Baseline Draft Analysis as authoritative ground truth.\n"
            f"- Use only metrics, numbers, and recommendations from the context and draft.\n"
            f"- Never invent metrics or contradict the draft.\n\n"
            f"Business Analytics Context:\n{ai_context}\n\n"
            f"User Question:\n{query}\n\n"
            f"Baseline Draft Analysis:\n{draft_answer}\n\n"
            f"Provide a helpful, executive-ready response."
        )

        # 1. Try OpenAI first
        if openai_key:
            openai_parts: List[str] = []
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key, max_retries=0)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert BI Agent assisting small business owners."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=700,
                    stream=on_chunk is not None,
                )
                if on_chunk is None:
                    return response.choices[0].message.content, "gpt-4o-mini"
                for event in response:
                    piece = event.choices[0].delta.content if event.choices else None
                    if piece:
                        openai_parts.append(piece)
                        on_chunk(piece)
                if openai_parts:
                    return "".join(openai_parts), "gpt-4o-mini"
            except Exception as e:
                logger.warning("OpenAI synthesis failed; falling back to Gemini (%s: %s)", type(e).__name__, str(e)[:80])
                if on_chunk is not None and openai_parts:
                    return "".join(openai_parts), "gpt-4o-mini (interrupted)"

        # 2. Try Gemini fallback (trying resilient models)
        if gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                gemini_models = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3.8-flash"]
                for g_model in gemini_models:
                    gemini_parts: List[str] = []
                    try:
                        if on_chunk is not None:
                            for event in client.models.generate_content_stream(model=g_model, contents=prompt):
                                if event.text:
                                    gemini_parts.append(event.text)
                                    on_chunk(event.text)
                            if gemini_parts:
                                return "".join(gemini_parts), g_model
                        else:
                            response = client.models.generate_content(model=g_model, contents=prompt)
                            if response.text:
                                return response.text, g_model
                    except Exception as gemini_err:
                        logger.debug("Gemini model %s failed: %s", g_model, gemini_err)
                        if gemini_parts:
                            return "".join(gemini_parts), f"{g_model} (interrupted)"
                        continue
            except Exception as e:
                logger.warning("Gemini synthesis fallback failed (%s)", type(e).__name__)

        # 3. If both failed, caller will use deterministic draft answer
        return None, None


    def _generate_arabic_response(
        self,
        intent: str,
        kpis: Dict[str, Any],
        breakdown: Dict[str, Any],
        customer_health: Dict[str, Any],
        inventory_risk: Dict[str, Any],
        trends: Dict[str, Any],
        date_range: str,
        query: str,
        source_name: Optional[str] = None,
        executed_sql: Optional[str] = None,
        sql_results: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, List[str]]:
        rev = kpis.get("revenue", {})
        ordr = kpis.get("orders", {})
        aov = self._get_aov_metric(kpis)
        canc = kpis.get("cancellation_rate", {})
        top_prods = breakdown.get("top_products", [])
        top_cats = breakdown.get("top_categories", [])

        rev_val = rev.get("current", 0)
        rev_pct = rev.get("percentage_change")
        rev_change_str = (
            f"{rev_pct:+.1f}% مقارنة بالفترة السابقة"
            if rev_pct is not None else "لا تتوفر بيانات سابقة"
        )

        if intent == "revenue_analysis":
            answer = (
                f"### 💰 تحليل الإيرادات والمبيعات\n\n"
                f"الفترة المحددة: `{date_range}`\n\n"
                f"- **إجمالي الإيرادات:** `{rev_val:,.2f}` ({rev_change_str})\n"
                f"- **الطلبات المكتملة:** `{ordr.get('current', 0)}` طلب\n"
                f"- **متوسط قيمة الطلب:** `{aov.get('current', 0):,.2f}`\n"
                f"- **معدل إلغاء الطلبات:** `{canc.get('current', 0)}%`\n\n"
            )
            if rev_pct is not None and rev_pct < 0:
                answer += f"⚠️ تراجعت الإيرادات بنسبة `{abs(rev_pct)}%` مقارنة بالفترة السابقة.\n\n"
            elif rev_pct is not None and rev_pct > 0:
                answer += f"🚀 نمت الإيرادات بنسبة `{rev_pct}%` مقارنة بالفترة السابقة.\n\n"
            followups = [
                "ما هي المنتجات الأكثر مبيعاً؟",
                "لماذا تغيرت الإيرادات؟",
                "ما هي التوصيات لزيادة المبيعات؟",
            ]
            return answer, followups

        elif intent == "aov_analysis":
            aov_metric = self._get_aov_metric(kpis)
            aov_change = aov_metric.get("percentage_change")
            change_text = f"{aov_change:+.1f}% مقارنة بالفترة السابقة" if aov_change is not None else "لا تتوفر فترة سابقة للمقارنة"
            answer = (
                f"### 🛒 متوسط قيمة الطلب\n\n"
                f"- **متوسط قيمة الطلب:** `{aov_metric.get('current', 0):,.2f}` دولار أمريكي ({change_text})\n"
                f"- **الإيرادات بالدولار:** `{rev_val:,.2f}`\n"
                f"- **الطلبات المكتملة:** `{ordr.get('current', 0)}`\n\n"
                "هذه قيمة مرصودة للفترة؛ البيانات الحالية لا تثبت سبب تغيرها أو ما إذا كانت مرتفعة بالنسبة لنشاطك."
            )
            return answer, ["ما المنتجات الأعلى في الإيرادات؟", "كيف تغيرت الإيرادات؟"]

        elif intent == "orders_analysis":
            order_metric = kpis.get("orders", {})
            order_change = order_metric.get("percentage_change")
            change_text = f"{order_change:+.1f}% مقارنة بالفترة السابقة" if order_change is not None else "لا تتوفر فترة سابقة للمقارنة"
            answer = (
                f"### 📦 تحليل الطلبات\n\n"
                f"- **الطلبات المكتملة:** `{order_metric.get('current', 0)}` ({change_text})\n"
                f"- **الإيرادات بالدولار:** `{rev_val:,.2f}`\n"
                f"- **معدل الإلغاء والاسترداد:** `{canc.get('current', 0)}%`\n\n"
            )
            if canc.get("total_order_attempts", 0) == 0:
                answer += "لا توجد محاولات طلب مسجلة لقياس معدل الإلغاء في هذه الفترة."
            else:
                answer += "معدل الإلغاء هنا مقارنة بحد التنبيه الداخلي 5%، وليس معيارًا عامًا لكل الأنشطة."
            return answer, ["لماذا أُلغيَت بعض الطلبات؟", "ما متوسط قيمة الطلب؟"]

        elif intent == "category_analysis":
            if top_cats:
                answer = "### 🗂️ أداء الفئات\n\n| الفئة | الإيرادات | الوحدات المباعة |\n| --- | ---: | ---: |\n"
                for category in top_cats[:5]:
                    answer += f"| {category.get('category') or 'غير مصنفة'} | {category.get('revenue', 0):,.2f} | {category.get('units_sold', 0)} |\n"
                answer += "\nهذه مقارنة بالإيرادات والوحدات المسجلة؛ لا تتضمن هامش الربح أو تكلفة المنتجات."
            else:
                answer = "لا تتوفر مبيعات مصنفة حسب الفئة لهذا المصدر والفترة."
            return answer, ["ما المنتجات الأعلى مبيعاً؟", "ما إجمالي الإيرادات؟"]

        elif intent == "trend_analysis":
            peak = trends.get("peak_revenue_day")
            low = trends.get("lowest_revenue_day")
            answer = f"### 📈 اتجاهات المبيعات اليومية\n\nتم تسجيل بيانات خلال `{trends.get('total_days_recorded', 0)}` يومًا.\n\n"
            if peak:
                answer += f"- **أعلى يوم مسجل:** `{peak['date']}` — `{peak['revenue']:,.2f}` دولار عبر `{peak['orders']}` طلبات.\n"
            if low:
                answer += f"- **أقل يوم مسجل:** `{low['date']}` — `{low['revenue']:,.2f}` دولار عبر `{low['orders']}` طلبات.\n"
            if not peak and not low:
                answer += "لا توجد سجلات يومية كافية لتحديد اتجاه."
            else:
                answer += "\nهذه مقارنة وصفية؛ البيانات لا تحدد سبب التغير اليومي."
            return answer, ["ما الذي غيّر الإيرادات؟", "ما الفئات الأعلى مبيعاً؟"]

        elif intent == "inventory_risk":
            inventory_products = inventory_risk.get("products", [])
            if inventory_products:
                top_one = inventory_products[0]
                answer = (
                    f"### 📦 تقييم خطر نفاد المخزون\n\n"
                    f"المنتج **{top_one['name']}** لديه حالياً `{top_one['stock_quantity']}` وحدة، "
                    f"وبِيع منه `{top_one['units_sold_last_30d']}` وحدة خلال آخر 30 يوماً. "
                    + (f"التغطية التقديرية نحو `{top_one['estimated_days_of_cover']}` يوماً. " if top_one.get("estimated_days_of_cover") is not None else "لا توجد مبيعات مسجلة في آخر 30 يوماً لحساب مدة التغطية. ")
                    + ("المنتج منخفض المخزون حسب البيانات المتاحة. " if top_one["at_risk"] else "لا يظهر حالياً ضمن المنتجات منخفضة المخزون. ")
                    + "هذا تقدير لا يشمل مدة توريد المورد أو مخزون الأمان."
                )
                if any(term in query.lower() for term in ("كمية", "أطلب", "اطلب", "إعادة الطلب", "اطلب تاني", "أعيد الطلب")):
                    answer += (
                        " لحساب كمية إعادة طلب مقترحة، أدخلي مدة توريد المورد ومخزون التغطية الإضافي؛ "
                        "يمكن تجهيز مسودة للمراجعة من قسم مخاطر المخزون."
                    )
            elif top_prods:
                top_one = top_prods[0]
                answer = (
                    f"### 📦 تقييم خطر نفاد المخزون\n\nالمنتج الأعلى مبيعاً هو **{top_one['name']}**، "
                    "لكن لا توجد كميات مخزون مستوردة لتقييم الخطر. ارفعي ملف المنتجات مع `stock_quantity` "
                    "واختيار نفس اسم مصدر بيانات المبيعات."
                )
            else:
                answer = (
                    "### 📦 تقييم خطر نفاد المخزون\n\n"
                    "لا أستطيع تقدير الخطر؛ لا توجد مبيعات منتجات لهذه الفترة، كما أن "
                    "البيانات لا تتضمن الكمية المتاحة حالياً أو مدة توريد المورد."
                )
            followups = [
                "كم وحدة من المنتج الأعلى مبيعاً متاحة حالياً؟",
                "ما بيانات المخزون اللازمة لحساب نقطة إعادة الطلب؟",
            ]
            return answer, followups

        elif intent == "product_analysis":
            answer = "### 🏆 المنتجات الأكثر مبيعاً\n\n"
            if top_prods:
                answer += "| المنتج | الوحدات المباعة | الإيرادات |\n| --- | --- | --- |\n"
                for p in top_prods[:5]:
                    answer += f"| **{p['name']}** | {p['units_sold']} | {p['revenue']:,.2f} |\n"
                top_one = top_prods[0]
                answer += f"\n⭐ المنتج الأول في المبيعات هو **{top_one['name']}** بإيرادات `{top_one['revenue']:,.2f}`.\n"
            else:
                answer += "لا تتوفر سجلات مبيعات منتجات في هذه الفترة.\n"
            followups = [
                "ما هي الفئات الأكثر مبيعاً؟",
                "ما إجمالي الإيرادات؟",
            ]
            return answer, followups

        elif intent == "customer_analysis":
            customer_count = customer_health.get("total_registered_customers", 0)
            rep_rate = customer_health.get("repeat_customer_rate_pct", 0.0)
            at_risk = customer_health.get("churn_at_risk_count", 0)
            active = customer_health.get("active_in_period", 0)
            answer = "### 👥 صحة قاعدة العملاء والولاء\n\n"
            if customer_count > 0:
                answer += (
                    f"- **سجلات العملاء:** `{customer_count}`\n"
                    f"- **معدل تكرار الشراء:** `{rep_rate}%`\n"
                    f"- **العملاء النشطون:** `{active}`\n"
                    f"- **العملاء المعرضون للانقطاع:** `{at_risk}` عميل\n\n"
                )
            else:
                answer += "لا توجد سجلات عملاء متاحة لهذا المصدر؛ لذلك لا يمكن حساب معدل تكرار الشراء أو مخاطر الانقطاع.\n\n"
            followups = [
                "من هم أكثر العملاء إنفاقاً؟",
                "كيف نرفع معدل الشراء المتكرر؟",
            ]
            return answer, followups

        elif intent == "winback_campaign":
            at_risk = customer_health.get("churn_at_risk_count", 0)
            customer_count = customer_health.get("total_registered_customers", 0)
            if customer_count == 0:
                answer = (
                    "### جمهور حملة إعادة التنشيط\n\n"
                    "لا أستطيع تحديد الجمهور؛ لا توجد سجلات عملاء لهذا المصدر. استوردي سجلات العملاء "
                    "المرتبطة بالطلبات قبل تخطيط حملة مخصصة. التطبيق لا يرسل رسائل تسويقية."
                )
            elif at_risk > 0:
                answer = (
                    "### خطة حملة إعادة تنشيط العملاء\n\n"
                    f"بيانات الشراء المتاحة تصنف `{at_risk}` عميلًا على أنهم لم يشتروا منذ أكثر من 60 يومًا. "
                    "التطبيق لا يرسل رسائل تسويقية؛ نفذي الخطوات التالية من منصة البريد أو CRM:\n\n"
                    "1. راجعي قائمة العملاء واستبعدي من لا يوافقون على تلقي الرسائل.\n"
                    "2. أرسلي رسالة متابعة مرتبطة بآخر عملية شراء للعميل.\n"
                    "3. اختبري عرضًا اختياريًا على مجموعة صغيرة قبل تعميمه.\n"
                    "4. قيسي الطلبات والإيرادات الناتجة، وأوقفي الحملة إن لم تحقق تحسنًا."
                )
            else:
                answer = (
                    "### جمهور حملة إعادة التنشيط\n\n"
                    "لا توجد حاليًا سجلات تصنف عملاء على أنهم غير نشطين لأكثر من 60 يومًا؛ "
                    "لذلك لا توجد شريحة استرجاع محددة في البيانات الحالية. راجعي حداثة الشراء في CRM "
                    "وحددي الشريحة قبل إطلاق الحملة. التطبيق لا يرسل رسائل تسويقية."
                )
            followups = [
                "كم عدد العملاء المعرضين للانقطاع؟",
                "ما معدل تكرار الشراء؟",
            ]
            return answer, followups

        elif intent == "anomaly_diagnosis":
            diagnoses = self.diagnose_anomalies(date_range, source_name)
            answer = "### 🔬 تشخيص الأسباب الجذرية للمؤشرات\n\n"
            for d in diagnoses:
                badge = "🔴" if d["severity"] == "danger" else "🟡"
                evidence = d.get("evidence", {})
                if d["id"] == "diag_insufficient_data":
                    title = "البيانات غير كافية للتشخيص"
                    summary = "لا توجد طلبات أو مبيعات منتجات لهذا المصدر والفترة، لذلك لا يمكن دعم تشخيص للنشاط."
                    causes = []
                    actions = ["استوردي سجلات الطلبات ومبيعات المنتجات للفترة المحددة، ثم أعيدي التشخيص."]
                elif d["id"] == "diag_revenue_decline":
                    title = "تراجع الإيرادات"
                    summary = f"انخفضت الإيرادات بنسبة {abs(d.get('change_pct') or 0):.1f}% مقارنة بالفترة السابقة."
                    causes = []
                    order_change = evidence.get("orders_change_pct")
                    aov_change = evidence.get("aov_change_pct")
                    if order_change is not None and order_change < 0:
                        causes.append(f"انخفض عدد الطلبات بنسبة {abs(order_change):.1f}%.")
                    if aov_change is not None and aov_change < 0:
                        causes.append(f"انخفض متوسط قيمة الطلب بنسبة {abs(aov_change):.1f}%. ")
                    if not causes:
                        causes.append("البيانات الحالية لا تحدد سببًا مؤكدًا للتراجع؛ يلزم فحص مصادر المبيعات والحملات بشكل منفصل.")
                    actions = [
                        "قارني الطلبات ومتوسط قيمة الطلب بين الفترتين لتحديد مصدر التراجع.",
                        "راجعي أداء المنتجات والفئات الأضعف خلال الفترة المحددة.",
                        "اختبري حملة استرجاع للعملاء السابقين، ثم قيسي أثرها على الطلبات والإيرادات.",
                    ]
                elif d["id"] == "diag_high_cancellations":
                    title = "ارتفاع إلغاء واسترداد الطلبات"
                    summary = f"معدل الإلغاء والاسترداد المسجل {d.get('current_value', 0)}% ({evidence.get('cancelled_orders_count', 0)} طلبًا)."
                    causes = [
                        "احتمالات تحتاج تحققًا: تعثر الدفع أو مشكلات إتمام الطلب.",
                        "قد تكون هناك مشكلة في وضوح مواعيد الشحن أو توقعات العميل؛ البيانات الحالية لا تؤكد السبب.",
                    ]
                    actions = [
                        "راجعي أسباب فشل الدفع وسجلات إلغاء الطلبات في منصة الدفع.",
                        "قارني معدلات الإلغاء حسب طريقة الدفع ومصدر الطلب إذا كانت هذه البيانات متاحة.",
                        "وضحي مواعيد الشحن وسياسة الإرجاع قبل إتمام الشراء.",
                    ]
                elif d["id"] == "diag_customer_retention":
                    title = "مخاطر تراجع تكرار الشراء"
                    summary = f"معدل تكرار الشراء {d.get('current_value', 0)}%، وهناك {evidence.get('churn_risk_count', 0)} عميلًا مصنفًا كمعرض للانقطاع."
                    causes = ["هذه مؤشرات من سجل الشراء؛ لا تحدد وحدها سبب توقف العميل عن الشراء."]
                    actions = [
                        "راجعي العملاء الذين لم يكرروا الشراء وحددي المنتجات التي اشتروها سابقًا.",
                        "اختبري رسالة متابعة أو عرضًا مناسبًا، ثم قيسي معدل العودة للشراء.",
                    ]
                elif d["id"] == "diag_healthy_status":
                    title = "الأداء مستقر"
                    summary = "لم تتجاوز المؤشرات المتاحة حدود التنبيه المعرّفة؛ وهذا لا يثبت أن كل العمليات سليمة."
                    causes = []
                    actions = ["واصلي متابعة المؤشرات المقاسة، وراجعي العمليات التي لا تغطيها البيانات المستوردة."]
                else:
                    title = d.get("title", "لا يتوفر تشخيص")
                    summary = d.get("summary", "لا تكفي البيانات المتاحة لتحديد السبب.")
                    causes = d.get("root_causes", [])
                    actions = d.get("mitigation_actions", [])

                answer += f"#### {badge} {title}\n{summary}\n\n"
                answer += "**عوامل محتملة تحتاج تحققًا:**\n"
                for rc in causes:
                    answer += f"- {rc}\n"
                answer += "\n**الإجراءات المقترحة:**\n"
                for act in actions:
                    answer += f"- {act}\n"
                answer += "\n"
            followups = [
                "ما هي التوصيات للتحسين؟",
                "ما هي المنتجات الأكثر مبيعاً؟",
            ]
            return answer, followups

        elif intent == "overview_summary":
            customer_count = customer_health.get("total_registered_customers", 0)
            answer = (
                f"### 📊 ملخص النشاط خلال `{date_range}`\n\n"
                f"- **الإيرادات:** `{rev_val:,.2f}` دولار أمريكي\n"
                f"- **الطلبات المكتملة:** `{ordr.get('current', 0)}`\n"
                f"- **متوسط قيمة الطلب:** `{aov.get('current', 0):,.2f}` دولار أمريكي\n"
                f"- **إلغاء/استرداد الطلبات:** `{canc.get('current', 0)}%`\n\n"
            )
            if customer_count:
                answer += (
                    f"- **سجلات العملاء:** `{customer_count}` | **تكرار الشراء:** `{customer_health.get('repeat_customer_rate_pct', 0)}%` | "
                    f"**معرضون للانقطاع:** `{customer_health.get('churn_at_risk_count', 0)}`\n\n"
                )
            else:
                answer += "بيانات الاحتفاظ بالعملاء غير متاحة؛ لا توجد سجلات عملاء مرتبطة بهذا المصدر.\n\n"
            if top_prods:
                answer += f"- **أعلى منتج بالإيرادات:** {top_prods[0]['name']} (`{top_prods[0]['revenue']:,.2f}` دولار)\n"
            elif not ordr.get("current", 0):
                answer += "لا توجد طلبات مكتملة لهذه الفترة والمصدر؛ بعض المؤشرات غير قابلة للتقييم.\n"
            return answer, ["ما المنتجات الأعلى مبيعاً؟", "ما التنبيهات الحالية؟"]

        elif intent == "recommendations":
            recs_data = self.generate_recommendations(date_range, source_name)
            answer = "### 📋 خطة العمل والتوصيات الاستراتيجية\n\n"
            if recs_data["total_recommendations"] == 0:
                answer += recs_data["executive_summary"]
                return answer, ["ما البيانات التي يجب استيرادها لبدء التحليل؟"]
            if any(term in query.lower() for term in ("profit", "profits", "margin", "أرباح", "الربح", "الأرباح")):
                answer += "ملاحظة: هذه اقتراحات لتحسين الإيرادات والطلبات، وليست حسابًا لصافي الربح؛ بيانات التكاليف والمصروفات غير متاحة.\n\n"
            repeat_summary = (
                f"معدل تكرار شراء `{customer_health.get('repeat_customer_rate_pct', 0)}%`"
                if customer_health.get("total_registered_customers", 0)
                else "عدم توفر سجلات العملاء لحساب تكرار الشراء"
            )
            answer += (
                f"بناءً على إيرادات قدرها `{rev_val:,.2f}` و`{ordr.get('current', 0)}` طلبًا، "
                f"و{repeat_summary}، "
                f"تم تحديد `{recs_data['total_recommendations']}` اقتراحات، منها "
                f"`{recs_data['high_priority_count']}` ذات أولوية مرتفعة.\n\n"
            )
            for r in recs_data.get("recommendations", [])[:3]:
                p_badge = "🔥 [أولوية قصوى]" if r["priority"] == "HIGH" else "⚡ [أولوية متوسطة]"
                if r["id"] == "rec_boost_aov_bundling":
                    product_name = top_prods[0]["name"] if top_prods else "المنتجات الأعلى مبيعًا"
                    title = f"اختبري عروضًا تجمع منتجات مكملة مع «{product_name}»"
                    impact = "قد يرتفع متوسط قيمة الطلب؛ اختبري الفكرة على نطاق صغير وقيسي النتيجة."
                    justification = f"متوسط قيمة الطلب الحالي `{aov.get('current', 0):,.2f}`. هذا اقتراح للاختبار وليس نتيجة مضمونة."
                    steps = [
                        f"اختاري منتجًا مكملًا مع «{product_name}» لتجربة العرض.",
                        "قارني متوسط قيمة الطلب قبل التجربة وبعدها.",
                        "أوقفي العرض أو عدليه إذا لم تتحسن النتائج.",
                    ]
                elif r["id"] == "rec_winback_churn_campaign":
                    at_risk = customer_health.get("churn_at_risk_count", 0)
                    title = f"اختبري حملة لإعادة تفاعل {at_risk} من العملاء المعرضين للانقطاع"
                    impact = "الهدف هو تحسين تكرار الشراء؛ قيسي عدد العملاء الذين عادوا للشراء."
                    justification = f"معدل تكرار الشراء المسجل `{customer_health.get('repeat_customer_rate_pct', 0)}%`، والعملاء المعرضون للانقطاع `{at_risk}`."
                    steps = [
                        "راجعي قائمة العملاء وتاريخ آخر عملية شراء.",
                        "أرسلي رسالة متابعة أو عرضًا مناسبًا للعملاء الذين لم يكرروا الشراء.",
                        "قيسي معدل العودة للشراء بعد الحملة.",
                    ]
                elif r["id"] == "rec_reduce_cancellations":
                    title = "راجعي أسباب إلغاء واسترداد الطلبات"
                    impact = "الهدف خفض معدل الإلغاء والاسترداد؛ لا تتوفر بيانات كافية لتقدير مبلغ مسترد."
                    justification = f"معدل الإلغاء والاسترداد المسجل `{canc.get('current', 0)}%`. البيانات الحالية لا تتضمن رموز فشل الدفع أو الإنفاق الإعلاني."
                    steps = [
                        "راجعي سجلات الدفع والإلغاء لتحديد الأسباب الفعلية.",
                        "وضحي وقت الشحن وسياسة الإرجاع عند إتمام الطلب.",
                        "تابعي معدل الإلغاء بعد تنفيذ التغيير.",
                    ]
                else:
                    category = top_cats[0].get("category", "الأعلى مبيعًا") if top_cats else "الأعلى مبيعًا"
                    title = f"اختبري توسيع المنتجات في فئة «{category}»"
                    impact = "قد يزيد مبيعات الفئة؛ تحققي من النتيجة بتجربة محدودة."
                    justification = f"الفئة «{category}» هي الأعلى في بيانات المبيعات المتاحة."
                    steps = [
                        f"راجعي المنتجات الأكثر مبيعًا داخل فئة «{category}».",
                        "اختبري منتجًا أو تنويعًا جديدًا على نطاق محدود.",
                        "قارني المبيعات قبل التجربة وبعدها.",
                    ]
                answer += f"#### {p_badge} {title}\n"
                answer += f"**النتيجة المحتملة:** {impact}\n\n_{justification}_\n\n"
                answer += "**خطوات التنفيذ:**\n"
                for step in steps:
                    answer += f"1. {step}\n"
                answer += "\n"
            followups = [
                "ما هي المنتجات الأكثر مبيعاً؟",
                "لماذا تراجعت الإيرادات؟",
            ]
            return answer, followups

        elif intent == "unsupported_profit_analysis":
            answer = (
                "### لا تتوفر بيانات كافية لحساب الأرباح\n\n"
                "أستطيع تحليل الإيرادات، لكن لا أستطيع حساب صافي الربح أو هامش الربح "
                "لأن البيانات الحالية لا تشمل تكلفة المنتجات أو مصروفات النشاط. "
                "أضيفي هذه البيانات أولًا حتى لا أعطيك رقمًا مضللًا."
            )
            followups = [
                "كم إجمالي الإيرادات؟",
                "ما المنتجات الأعلى في الإيرادات؟",
                "ما متوسط قيمة الطلب؟",
            ]
            return answer, followups

        else:
            answer = (
                f"### 🤖 المساعد التحليلي الذكي\n\n"
                f"لم أتمكن من ربط سؤالك *\"{query}\"* بتحليل مدعوم حاليًا. "
                "أستطيع تحليل الإيرادات والطلبات والمنتجات والعملاء والاتجاهات وجودة البيانات، "
                "أو تقديم توصيات بناءً على هذه البيانات.\n\n"
                "جرّبي سؤالًا مثل:\n"
                f"- *كم إجمالي الإيرادات؟*\n"
                f"- *ما هي المنتجات الأكثر مبيعاً؟*\n"
                f"- *ما هي التوصيات لزيادة الأرباح؟*\n"
                f"- *لماذا انخفضت المبيعات؟*\n"
            )
            followups = [
                "ما هي المنتجات الأكثر مبيعاً؟",
                "ما هي التوصيات لزيادة الأرباح؟",
            ]
            return answer, followups

    # -----------------------------------------------------------------------
    # Contextual Suggestions
    # -----------------------------------------------------------------------

    def get_suggested_queries(
        self,
        date_range: str = "30d",
        source_name: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Returns contextual quick-prompt pills tailored to current business conditions."""
        ai_context = self.analytics_svc.get_ai_context(date_range, source_name)
        kpis = ai_context["headline_kpis"]
        customer_health = ai_context["customer_health"]

        suggestions = [
            {
                "category": "Revenue & Sales",
                "prompt": "What is our total revenue and how does it compare to the prior period?",
                "icon": "DollarSign",
            },
            {
                "category": "Products",
                "prompt": "Which products are generating the highest revenue and units sold?",
                "icon": "Package",
            },
            {
                "category": "Retention",
                "prompt": "How many repeat customers do we have, and which ones are at risk of churning?",
                "icon": "Users",
            },
            {
                "category": "Action Plan",
                "prompt": "Give me 3 prioritized recommendations to increase our sales and margins.",
                "icon": "Sparkles",
            },
        ]

        # Context-dependent dynamic suggestion
        rev_pct = kpis["revenue"]["percentage_change"]
        if rev_pct is not None and rev_pct < -5.0:
            suggestions.insert(0, {
                "category": "Anomaly Alert",
                "prompt": "Why did our revenue decline this period? Diagnose root causes.",
                "icon": "AlertTriangle",
            })
        elif kpis["cancellation_rate"]["current"] >= 5.0:
            suggestions.insert(0, {
                "category": "Anomaly Alert",
                "prompt": "Why is our cancellation rate high? Investigate causes.",
                "icon": "AlertOctagon",
            })

        return suggestions[:5]
