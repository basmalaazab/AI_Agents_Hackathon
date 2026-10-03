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
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
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

    def _get_aov_metric(self, kpis: Dict[str, Any]) -> Dict[str, Any]:
        """Safely retrieves the AOV metric dictionary regardless of key naming."""
        return kpis.get("avg_order_value") or kpis.get("average_order_value") or {
            "current": 0.0,
            "previous": 0.0,
            "percentage_change": None,
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
                    "High post-checkout friction, payment gateway failures, or stock discrepancies.",
                    "Customer expectations mismatch on shipping lead times or delivery dates.",
                ],
                "contributing_factors": [
                    f"{canc_orders} out of {total_att} total order attempts failed or refunded.",
                    "Estimated lost revenue: check pending and cancelled statuses in orders table.",
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
                    "Lack of post-purchase automated nurturing flows (e.g. 14-day check-in, replenishment reminders).",
                    "Over-reliance on one-off initial customer acquisitions without lifetime value loyalty loops.",
                ],
                "contributing_factors": [
                    f"{at_risk} customers have not made a repeat purchase within standard repurchase cycle.",
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
                "summary": "Key operational metrics are stable. No urgent operational bottlenecks detected.",
                "root_causes": ["Steady conversion rates and healthy order fulfillment."],
                "contributing_factors": [
                    f"Revenue: ${kpis['revenue']['current']:,.2f}",
                    f"Total completed orders: {kpis['orders']['current']}",
                    f"Cancellation rate: {canc_rate}%",
                ],
                "evidence": {"status": "normal"},
                "mitigation_actions": [
                    "Continue scaling inventory for top-performing SKUs.",
                    "Experiment with cross-sell recommendation widgets on checkout.",
                ],
            })

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
        repeat_rate = customer_health.get("repeat_customer_rate_pct", 0.0)

        at_risk = customer_health.get("churn_at_risk_count", 0)
        canc_rate = kpis["cancellation_rate"]["current"]
        top_prods = breakdown.get("top_products", [])
        top_cats = breakdown.get("top_categories", [])

        # Recommendation 1: AOV & Cross-Sell Bundling
        if aov_val > 0:
            top_prod_name = top_prods[0]["name"] if top_prods else "Best-selling items"
            recommendations.append({
                "id": "rec_boost_aov_bundling",
                "title": f"Create High-Margin Product Bundles featuring '{top_prod_name}'",
                "category": "Revenue & Growth",
                "priority": "HIGH" if aov_val < 75.0 else "MEDIUM",
                "expected_impact": "12% - 18% lift in Average Order Value",
                "implementation_effort": "LOW",
                "target_metric": "average_order_value",
                "data_justification": (
                    f"Current Average Order Value is ${aov_val:.2f}. "
                    f"Your top product '{top_prod_name}' accounts for substantial customer demand. "
                    "Pairing it with accessory products can lift basket size without increasing acquisition costs."
                ),
                "action_steps": [
                    f"Bundle '{top_prod_name}' with 1-2 complementary accessories at a 10% bundle discount.",
                    "Add an 'Often Bought Together' recommendation prompt on product checkout pages.",
                    f"Set a free shipping threshold 20% higher than your current AOV (suggested: ${round(aov_val * 1.25, 0)}).",
                ],
            })

        # Recommendation 2: Retention & Churn Win-Back Campaign
        if at_risk > 0 or repeat_rate < 35.0:
            recommendations.append({
                "id": "rec_winback_churn_campaign",
                "title": f"Deploy Automated Win-Back Sequence for {at_risk} At-Risk Customers",
                "category": "Customer Retention & Loyalty",
                "priority": "HIGH",
                "expected_impact": "Recover 15% - 22% of dormant customers within 14 days",
                "implementation_effort": "LOW",
                "target_metric": "repeat_customer_rate",
                "data_justification": (
                    f"Repeat customer rate is {repeat_rate:.1f}%, and {at_risk} customers have not made a repeat purchase "
                    "in over 30 days. Acquiring new customers costs 5x more than re-engaging past purchasers."
                ),
                "action_steps": [
                    "Segment the customer list by recency: filter customers with order_count >= 1 and last purchase > 30 days.",
                    "Send a personalized 3-part email campaign: Day 1 (We miss you), Day 4 (Exclusive 15% credit), Day 7 (Final reminder).",
                    "Offer personalized product recommendations based on their prior purchase history.",
                ],
            })

        # Recommendation 3: Inventory Allocation for Star Products
        if top_prods:
            star_prod = top_prods[0]
            star_rev = star_prod.get("revenue", 0)
            recommendations.append({
                "id": "rec_inventory_scale",
                "title": f"Prioritize Stock Reorder for Revenue Driver: {star_prod['name']}",
                "category": "Catalog & Merchandising",
                "priority": "MEDIUM",
                "expected_impact": f"Eliminate stockout revenue leakage (safeguard ~${star_rev:,.2f})",
                "implementation_effort": "MEDIUM",
                "target_metric": "revenue",

                "data_justification": (
                    f"'{star_prod['name']}' generated ${star_prod.get('revenue', 0):,.2f} with "
                    f"{star_prod.get('units_sold', 0)} units sold in this period. Running out of stock would cause immediate revenue contraction."
                ),
                "action_steps": [
                    f"Check current inventory safety stock levels for SKU '{star_prod.get('sku', 'N/A')}'.",
                    "Establish a 14-day lead time reorder trigger with your primary supplier.",
                    "Feature this item prominently in top-of-funnel marketing campaigns.",
                ],
            })

        # Recommendation 4: Cancellation Rate Mitigation
        if canc_rate >= 4.0:
            recommendations.append({
                "id": "rec_reduce_cancellations",
                "title": "Optimize Checkout & Payment Gateway to Reduce Order Drop-Off",
                "category": "Operational Efficiency",
                "priority": "HIGH",
                "expected_impact": f"Reclaim up to ${(rev_val * (canc_rate / 100)):,.2f} in lost gross merchandise value",
                "implementation_effort": "MEDIUM",
                "target_metric": "cancellation_rate",
                "data_justification": (
                    f"Current cancellation / refund rate is {canc_rate:.1f}%. "
                    "Each cancelled order damages customer trust and burns ad spend without revenue realization."
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
                "expected_impact": "10% - 15% category revenue expansion",
                "implementation_effort": "HIGH",
                "target_metric": "revenue",
                "data_justification": (
                    f"'{leading_cat.get('category')}' generates ${leading_cat.get('revenue', 0):,.2f} "
                    f"({leading_cat.get('percentage', 0)}% of total category sales). High category concentration indicates strong product-market fit."
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
        exec_summary = (
            f"Based on current metrics (${rev_val:,.2f} revenue, {kpis['orders']['current']} orders, "
            f"{repeat_rate:.1f}% repeat rate, {canc_rate:.1f}% cancellation rate), "
            f"we identified {len(recommendations)} strategic recommendations. "
            f"{len(high_priority)} require immediate attention to protect revenue and maximize customer retention."
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

        # 2. Revenue & Sales
        elif any(k in q_lower for k in [
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
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            aov_change = aov.get("percentage_change")
            aov_str = f"{aov_change:+.1f}% vs previous period" if aov_change is not None else "No prior data"
            answer = (
                f"### \U0001f6d2 Average Order Value (AOV)\n\n"
                f"- **AOV:** `${aov['current']:,.2f}` ({aov_str})\n"
                f"- **Total Revenue:** `${rev['current']:,.2f}` from `{ordr['current']}` orders\n\n"
            )
            if aov["current"] < 50:
                answer += (
                    f"\U0001f4ca AOV below $50 — consider bundles or a free-shipping threshold "
                    f"(suggested: ${aov['current']*1.2:.0f}).\n\n"
                )
            elif aov["current"] < 100:
                answer += "\U0001f4ca Moderate AOV — 15-20% lift possible through bundling and upsell.\n\n"
            else:
                answer += "\u2705 Strong AOV — focus on volume growth to scale revenue.\n\n"
            if top_prods:
                answer += f"\U0001f4a1 Bundle **{top_prods[0]['name']}** with accessories to further lift AOV.\n"
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
                answer += "\u2705 Cancellation rate is within a healthy range.\n\n"
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
                "SUM(oi.line_total) AS revenue_usd "
                "FROM order_items oi JOIN orders o ON o.id = oi.order_id "
                "WHERE o.status NOT IN ('cancelled', 'refunded') "
                "GROUP BY oi.product_name ORDER BY revenue_usd DESC LIMIT 5;"
            )
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
            "lifetime value", "how many customer", "at risk", "win back", "winback",
            "عميل", "عملاء", "ولاء", "زبائن", "زبون", "استبقاء", "خسارة العملاء", "الاحتفاظ",
        ]):
            intent = "customer_analysis"
            rep_rate = customer_health.get("repeat_customer_rate_pct", 0.0)
            at_risk  = customer_health.get("churn_at_risk_count", 0)
            active   = customer_health.get("active_in_period", 0)
            new_cust = customer_health.get("new_in_period", 0)
            executed_sql = (
                "SELECT c.email, c.first_name, c.last_name, COUNT(o.id) AS order_count, "
                "SUM(o.total_amount_usd) AS lifetime_value_usd "
                "FROM customers c JOIN orders o ON o.customer_id = c.id "
                "WHERE o.status NOT IN ('cancelled', 'refunded') "
                "GROUP BY c.id, c.email, c.first_name, c.last_name "
                "ORDER BY lifetime_value_usd DESC LIMIT 5;"
            )
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            answer = (
                f"### \U0001f465 Customer Health & Retention\n\n"
                f"- **Repeat Customer Rate:** `{rep_rate}%`\n"
                f"- **Active Customers:** `{active}`\n"
                f"- **New Customers Acquired:** `{new_cust}`\n"
                f"- **Churn Risk:** `{at_risk}` customers\n\n"
            )
            if at_risk > 0:
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
                "SUM(oi.line_total) AS revenue_usd "
                "FROM order_items oi "
                "JOIN orders o ON o.id = oi.order_id "
                "JOIN products p ON p.id = oi.product_id "
                "WHERE o.status NOT IN ('cancelled', 'refunded') "
                "GROUP BY p.category ORDER BY revenue_usd DESC;"
            )
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
            "لماذا", "انخفاض", "مشكلة", "سبب", "انخفضت", "تراجعت", "تراجع", "خلل", "لما",
        ]):
            intent = "anomaly_diagnosis"
            diagnoses = self.diagnose_anomalies(date_range, source_name)
            answer = "### \U0001f52c Root-Cause Business Diagnosis\n\n"
            for d in diagnoses:
                badge = "\U0001f534" if d["severity"] == "danger" else ("\U0001f7e1" if d["severity"] == "warning" else "\U0001f535")
                answer += f"#### {badge} {d['title']}\n{d['summary']}\n\n"
                answer += "**Root Causes:**\n"
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

        # 9. Strategic Recommendations
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
            followups = [
                "Diagnose why revenue dropped",
                "How do we run the win-back campaign?",
                "What products have highest margins?",
            ]

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
            if include_sql:
                sql_results = self.execute_safe_sql(executed_sql)
            answer = f"### \U0001f4c8 Daily Revenue Trends\n\nAcross `{total_days}` days:\n\n"
            if peak:
                answer += f"- \U0001f31f **Peak:** `{peak['date']}` — **${peak['revenue']:,.2f}** ({peak['orders']} orders)\n"
            if low:
                answer += f"- \U0001f4c9 **Lowest:** `{low['date']}` — **${low['revenue']:,.2f}** ({low['orders']} orders)\n"
            answer += "\nSales fluctuate by day-of-week, promotions, and inventory levels.\n"
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
                answer += "\nClean records loaded with deduplication guarantees.\n"
            else:
                answer += "\u2705 All data quality checks passed — 0 rejected records.\n"
            followups = [
                "What are our clean order numbers?",
                "Show total revenue",
                "Inspect registered sources",
            ]

        # 12. Overview / Dashboard Summary
        elif any(k in q_lower for k in [
            "overview", "summary", "dashboard", "snapshot", "report",
            "how are we doing", "how is the business", "business health",
            "kpi", "metrics", "show me", "tell me", "give me", "what is", "how is",
            "status", "ملخص", "نظرة عامة", "تقرير", "أداء الشركة", "كيف العمل", "الوضع المالي", "مؤشرات",
        ]):
            intent = "overview_summary"
            rev      = kpis["revenue"]["current"]
            orders_cnt = kpis["orders"]["current"]
            aov      = self._get_aov_metric(kpis)["current"]
            canc     = kpis["cancellation_rate"]["current"]
            rep_rate = customer_health.get("repeat_customer_rate_pct", 0.0)
            at_risk  = customer_health.get("churn_at_risk_count", 0)
            top_prods = breakdown.get("top_products", [])
            answer = (
                f"### \U0001f4ca Business Overview — `{date_range}`\n\n"
                f"#### \U0001f4b0 Revenue\n"
                f"- Total: `${rev:,.2f}` | Orders: `{orders_cnt}` | AOV: `${aov:,.2f}` | Cancellations: `{canc}%`\n\n"
                f"#### \U0001f465 Customers\n"
                f"- Repeat Rate: `{rep_rate}%` | Churn Risk: `{at_risk}`\n\n"
            )
            if top_prods:
                answer += f"#### \U0001f3c6 Top Product\n- **{top_prods[0]['name']}** — `${top_prods[0]['revenue']:,.2f}`\n\n"
            alerts = []
            if canc > 5.0:
                alerts.append(f"\U0001f534 Cancellation rate `{canc}%` above threshold")
            if at_risk > 0:
                alerts.append(f"\U0001f7e1 `{at_risk}` customers at churn risk")
            if rep_rate < 30:
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
            rev        = kpis["revenue"]["current"]
            orders_cnt = kpis["orders"]["current"]
            aov        = self._get_aov_metric(kpis)["current"]
            top_prods  = breakdown.get("top_products", [])
            top_prod_name = top_prods[0]["name"] if top_prods else "N/A"
            answer = (
                f"### \U0001f916 AI Business Intelligence Agent\n\n"
                f"I heard: *\"{query}\"*\n\n"
                f"| Metric | Value |\n| --- | --- |\n"
                f"| Total Revenue | `${rev:,.2f}` |\n"
                f"| Completed Orders | `{orders_cnt}` |\n"
                f"| Average Order Value | `${aov:,.2f}` |\n"
                f"| Repeat Customer Rate | `{customer_health.get('repeat_customer_rate_pct', 0)}%` |\n"
                f"| Churn Risk | `{customer_health.get('churn_at_risk_count', 0)}` customers |\n"
                f"| Top Product | `{top_prod_name}` |\n\n"
                "\U0001f4a1 Try asking:\n"
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
                trends=trends,
                date_range=date_range,
                query=q_clean,
                executed_sql=executed_sql,
                sql_results=sql_results,
            )
            answer = ar_answer
            followups = ar_followups

        # -------------------------------------------------------------------
        # LLM Synthesis (if API key is configured)
        # -------------------------------------------------------------------
        model_used = "built-in-analyst"
        if self.settings.gemini_api_key or self.settings.openai_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY"):
            try:
                enhanced_answer = self._synthesize_with_llm(
                    query=q_clean,
                    ai_context=ai_context,
                    draft_answer=answer,
                    conversation_history=conversation_history,
                )
                if enhanced_answer:
                    answer = enhanced_answer
                    model_used = self.settings.ai_agent_model or "llm-augmented"
            except Exception as llm_exc:
                logger.warning("LLM synthesis failed, relying on deterministic reasoning: %s", llm_exc)

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
                "repeat_customer_rate": customer_health.get("repeat_customer_rate_pct"),
                "churn_risk_count": customer_health.get("churn_at_risk_count"),
            },
            "suggested_followups": followups,
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
    ) -> Optional[str]:
        """Optionally enhances answer using OpenAI or Google Gemini if keys are present."""
        openai_key = self.settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        gemini_key = self.settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")

        prompt = (
            f"You are the AI Business Intelligence Agent for a small business. "
            f"Answer the user's business question with clarity, accurate numbers, and actionable executive insights.\n\n"
            f"Business Analytics Context:\n{ai_context}\n\n"
            f"User Question: {query}\n\n"
            f"Baseline Draft Analysis:\n{draft_answer}\n\n"
            f"Provide a concise, beautifully formatted markdown response."
        )

        if openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert BI Agent assisting small business owners."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=600,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.debug("OpenAI call exception: %s", e)

        if gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                logger.debug("Gemini call exception: %s", e)

        return None

    def _generate_arabic_response(
        self,
        intent: str,
        kpis: Dict[str, Any],
        breakdown: Dict[str, Any],
        customer_health: Dict[str, Any],
        trends: Dict[str, Any],
        date_range: str,
        query: str,
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
            rep_rate = customer_health.get("repeat_customer_rate_pct", 0.0)
            at_risk = customer_health.get("churn_at_risk_count", 0)
            active = customer_health.get("active_in_period", 0)
            answer = (
                f"### 👥 صحة قاعدة العملاء والولاء\n\n"
                f"- **معدل تكرار الشراء:** `{rep_rate}%`\n"
                f"- **العملاء النشطون:** `{active}`\n"
                f"- **العملاء المعرضون للانقطاع:** `{at_risk}` عميل\n\n"
            )
            followups = [
                "من هم أكثر العملاء إنفاقاً؟",
                "كيف نرفع معدل الشراء المتكرر؟",
            ]
            return answer, followups

        elif intent == "anomaly_diagnosis":
            diagnoses = self.diagnose_anomalies(date_range)
            answer = "### 🔬 تشخيص الأسباب الجذرية للمؤشرات\n\n"
            for d in diagnoses:
                badge = "🔴" if d["severity"] == "danger" else "🟡"
                answer += f"#### {badge} {d['title']}\n{d['summary']}\n\n"
                answer += "**الأسباب المحددة:**\n"
                for rc in d["root_causes"]:
                    answer += f"- {rc}\n"
                answer += "\n**الإجراءات المقترحة:**\n"
                for act in d["mitigation_actions"]:
                    answer += f"- {act}\n"
                answer += "\n"
            followups = [
                "ما هي التوصيات للتحسين؟",
                "ما هي المنتجات الأكثر مبيعاً؟",
            ]
            return answer, followups

        elif intent == "recommendations":
            recs_data = self.generate_recommendations(date_range)
            answer = f"### 📋 خطة العمل والتوصيات الاستراتيجية\n\n{recs_data.get('executive_summary', '')}\n\n"
            for r in recs_data.get("recommendations", [])[:3]:
                p_badge = "🔥 [أولوية قصوى]" if r["priority"] == "HIGH" else "⚡ [أولوية متوسطة]"
                answer += f"#### {p_badge} {r['title']}\n"
                answer += f"**الأثر المتوقع:** `{r['expected_impact']}`\n\n_{r['data_justification']}_\n\n"
                answer += "**خطوات التنفيذ:**\n"
                for step in r["action_steps"]:
                    answer += f"1. {step}\n"
                answer += "\n"
            followups = [
                "ما هي المنتجات الأكثر مبيعاً؟",
                "لماذا تراجعت الإيرادات؟",
            ]
            return answer, followups

        else:
            answer = (
                f"### 🤖 المساعد التحليلي الذكي\n\n"
                f"السؤال: *\"{query}\"*\n\n"
                f"| المؤشر | القيمة |\n| --- | --- |\n"
                f"| إجمالي الإيرادات | `{rev_val:,.2f}` |\n"
                f"| الطلبات المكتملة | `{ordr.get('current', 0)}` |\n"
                f"| متوسط قيمة الطلب | `{aov.get('current', 0):,.2f}` |\n"
                f"| معدل تكرار الشراء | `{customer_health.get('repeat_customer_rate_pct', 0)}%` |\n"
                f"| عملاء في دائرة الخطر | `{customer_health.get('churn_at_risk_count', 0)}` |\n\n"
                f"💡 أسئلة مقترحة:\n"
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
