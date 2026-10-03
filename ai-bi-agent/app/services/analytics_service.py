"""
Analytics Service — Core Business Intelligence & Transformation Engine.

Calculates business metrics, time-series aggregations, period-over-period comparisons,
customer retention/cohort statistics, business anomaly alerts, and structured data
payloads for Person 3's AI Agent.
"""
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import Result, and_, case, func, or_, text
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------------------
    # Date Range Helpers
    # ---------------------------------------------------------------------------

    @staticmethod
    def resolve_date_range(
        preset: str = "30d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Tuple[Optional[datetime], Optional[datetime], Optional[datetime], Optional[datetime]]:
        """
        Resolves a date range preset or explicit dates into:
        (curr_start, curr_end, prev_start, prev_end) in UTC.
        """
        now = datetime.now(timezone.utc)
        curr_end: Optional[datetime] = now
        curr_start: Optional[datetime] = None

        preset_lower = (preset or "30d").lower()

        if preset_lower == "today":
            curr_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        elif preset_lower == "7d":
            curr_start = now - timedelta(days=7)
        elif preset_lower == "30d":
            curr_start = now - timedelta(days=30)
        elif preset_lower == "3m":
            curr_start = now - timedelta(days=90)
        elif preset_lower == "6m":
            curr_start = now - timedelta(days=180)
        elif preset_lower == "12m":
            curr_start = now - timedelta(days=365)
        elif preset_lower == "custom" and start_date:
            try:
                curr_start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                if not curr_start.tzinfo:
                    curr_start = curr_start.replace(tzinfo=timezone.utc)
            except ValueError:
                curr_start = now - timedelta(days=30)
            
            if end_date:
                try:
                    curr_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    if not curr_end.tzinfo:
                        curr_end = curr_end.replace(tzinfo=timezone.utc)
                except ValueError:
                    curr_end = now
        elif preset_lower == "all":
            curr_start = None
            curr_end = None

        # Compute prior period of equal length
        prev_start: Optional[datetime] = None
        prev_end: Optional[datetime] = None

        if curr_start and curr_end:
            duration = curr_end - curr_start
            prev_end = curr_start
            prev_start = curr_start - duration

        return curr_start, curr_end, prev_start, prev_end

    # ---------------------------------------------------------------------------
    # Overview KPIs & Period-over-Period Growth
    # ---------------------------------------------------------------------------

    def get_overview_kpis(
        self,
        date_range: str = "30d",
        source_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns headline KPIs (Revenue, Orders, AOV, Customers) along with
        period-over-period absolute and percentage changes.
        """
        c_start, c_end, p_start, p_end = self.resolve_date_range(date_range, start_date, end_date)

        curr_stats = self._query_period_metrics(c_start, c_end, source_name)
        prev_stats = self._query_period_metrics(p_start, p_end, source_name) if (p_start and p_end) else None

        return {
            "period": {
                "preset": date_range,
                "current_start": c_start.isoformat() if c_start else None,
                "current_end": c_end.isoformat() if c_end else None,
                "previous_start": p_start.isoformat() if p_start else None,
                "previous_end": p_end.isoformat() if p_end else None,
            },
            "kpis": {
                "revenue": self._build_kpi_metric(curr_stats["revenue"], prev_stats["revenue"] if prev_stats else None, is_currency=True),
                "orders": self._build_kpi_metric(curr_stats["orders"], prev_stats["orders"] if prev_stats else None),
                "avg_order_value": self._build_kpi_metric(curr_stats["aov"], prev_stats["aov"] if prev_stats else None, is_currency=True),
                "active_customers": self._build_kpi_metric(curr_stats["unique_customers"], prev_stats["unique_customers"] if prev_stats else None),
                "cancellation_rate": {
                    "current": curr_stats["cancellation_rate"],
                    "previous": prev_stats["cancellation_rate"] if prev_stats else 0.0,
                    "cancelled_orders": curr_stats["cancelled_count"],
                    "total_order_attempts": curr_stats["total_attempts"],
                },
            },
        }

    def _query_period_metrics(
        self,
        start_dt: Optional[datetime],
        end_dt: Optional[datetime],
        source_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = self.db.query(Order)
        if start_dt:
            query = query.filter(Order.order_date >= start_dt)
        if end_dt:
            query = query.filter(Order.order_date <= end_dt)
        if source_name:
            query = query.filter(Order.source_name == source_name)

        all_orders = query.all()
        if not all_orders:
            return {
                "revenue": 0.0,
                "orders": 0,
                "aov": 0.0,
                "unique_customers": 0,
                "cancelled_count": 0,
                "total_attempts": 0,
                "cancellation_rate": 0.0,
            }

        valid_orders = [o for o in all_orders if o.status not in ("cancelled", "refunded")]
        cancelled_orders = [o for o in all_orders if o.status in ("cancelled", "refunded")]

        total_rev = sum(float(o.total_amount_usd or o.total_amount or 0) for o in valid_orders)
        order_count = len(valid_orders)
        aov = (total_rev / order_count) if order_count > 0 else 0.0
        unique_custs = len({o.customer_id for o in valid_orders if o.customer_id})

        total_attempts = len(all_orders)
        canc_count = len(cancelled_orders)
        canc_rate = round((canc_count / total_attempts * 100), 2) if total_attempts > 0 else 0.0

        return {
            "revenue": round(total_rev, 2),
            "orders": order_count,
            "aov": round(aov, 2),
            "unique_customers": unique_custs,
            "cancelled_count": canc_count,
            "total_attempts": total_attempts,
            "cancellation_rate": canc_rate,
        }

    @staticmethod
    def _build_kpi_metric(curr: float, prev: Optional[float] = None, is_currency: bool = False) -> Dict[str, Any]:
        curr_val = round(curr, 2) if is_currency else round(curr, 0)
        if prev is None:
            return {
                "current": curr_val,
                "previous": None,
                "absolute_change": None,
                "percentage_change": None,
            }
        
        prev_val = round(prev, 2) if is_currency else round(prev, 0)
        abs_change = round(curr_val - prev_val, 2)
        pct_change = round(((curr_val - prev_val) / prev_val * 100), 2) if prev_val > 0 else (100.0 if curr_val > 0 else 0.0)

        return {
            "current": curr_val,
            "previous": prev_val,
            "absolute_change": abs_change,
            "percentage_change": pct_change,
        }

    # ---------------------------------------------------------------------------
    # Time-Series Revenue & Sales Trends
    # ---------------------------------------------------------------------------

    def get_revenue_trends(
        self,
        date_range: str = "30d",
        source_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns time-series revenue, order counts, and AOV grouped by date.
        """
        c_start, c_end, _, _ = self.resolve_date_range(date_range, start_date, end_date)

        query = (
            self.db.query(
                func.date(Order.order_date).label("sale_date"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total_amount_usd), 0).label("revenue_usd"),
            )
            .filter(~Order.status.in_(["cancelled", "refunded"]))
        )

        if c_start:
            query = query.filter(Order.order_date >= c_start)
        if c_end:
            query = query.filter(Order.order_date <= c_end)
        if source_name:
            query = query.filter(Order.source_name == source_name)

        query = query.group_by(func.date(Order.order_date)).order_by(func.date(Order.order_date).asc())

        rows = query.all()
        result = []
        for r in rows:
            orders = int(r.order_count or 0)
            rev = float(r.revenue_usd or 0)
            aov = round(rev / orders, 2) if orders > 0 else 0.0
            result.append({
                "date": str(r.sale_date),
                "revenue": round(rev, 2),
                "orders": orders,
                "avg_order_value": aov,
            })
        return result

    # ---------------------------------------------------------------------------
    # Sales & Category Breakdown
    # ---------------------------------------------------------------------------

    def get_sales_breakdown(
        self,
        date_range: str = "30d",
        source_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns breakdowns of sales by Product Category, Source Platform, and Top Products.
        """
        c_start, c_end, _, _ = self.resolve_date_range(date_range, start_date, end_date)

        # 1. By Category (joining OrderItem -> Product & Order)
        cat_query = (
            self.db.query(
                func.coalesce(Product.category, "Uncategorized").label("category"),
                func.sum(OrderItem.quantity).label("units_sold"),
                func.coalesce(func.sum(OrderItem.line_total), 0).label("revenue"),
                func.count(func.distinct(OrderItem.order_id)).label("order_count"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .outerjoin(Product, Product.id == OrderItem.product_id)
            .filter(~Order.status.in_(["cancelled", "refunded"]))
        )
        if c_start:
            cat_query = cat_query.filter(Order.order_date >= c_start)
        if c_end:
            cat_query = cat_query.filter(Order.order_date <= c_end)
        if source_name:
            cat_query = cat_query.filter(Order.source_name == source_name)

        cat_rows = cat_query.group_by("category").order_by(text("revenue DESC")).all()

        total_cat_rev = sum(float(r.revenue or 0) for r in cat_rows)
        categories = [
            {
                "category": r.category,
                "units_sold": int(r.units_sold or 0),
                "revenue": round(float(r.revenue or 0), 2),
                "order_count": int(r.order_count or 0),
                "percentage_of_total": round((float(r.revenue or 0) / total_cat_rev * 100), 2) if total_cat_rev > 0 else 0.0,
            }
            for r in cat_rows
        ]

        # 2. By Source / Platform
        platform_query = (
            self.db.query(
                Order.source_name.label("platform"),
                func.count(Order.id).label("orders"),
                func.coalesce(func.sum(Order.total_amount_usd), 0).label("revenue"),
            )
            .filter(~Order.status.in_(["cancelled", "refunded"]))
        )
        if c_start:
            platform_query = platform_query.filter(Order.order_date >= c_start)
        if c_end:
            platform_query = platform_query.filter(Order.order_date <= c_end)
        if source_name:
            platform_query = platform_query.filter(Order.source_name == source_name)

        platform_rows = platform_query.group_by(Order.source_name).order_by(text("revenue DESC")).all()
        platforms = [
            {
                "platform": r.platform,
                "orders": int(r.orders or 0),
                "revenue": round(float(r.revenue or 0), 2),
            }
            for r in platform_rows
        ]

        # 3. Top Products
        top_prod_query = (
            self.db.query(
                OrderItem.product_name,
                OrderItem.sku,
                func.coalesce(Product.category, "General").label("category"),
                func.sum(OrderItem.quantity).label("units_sold"),
                func.coalesce(func.sum(OrderItem.line_total), 0).label("revenue"),
                func.count(func.distinct(OrderItem.order_id)).label("order_count"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .outerjoin(Product, Product.id == OrderItem.product_id)
            .filter(~Order.status.in_(["cancelled", "refunded"]))
        )
        if c_start:
            top_prod_query = top_prod_query.filter(Order.order_date >= c_start)
        if c_end:
            top_prod_query = top_prod_query.filter(Order.order_date <= c_end)
        if source_name:
            top_prod_query = top_prod_query.filter(Order.source_name == source_name)

        top_prod_rows = top_prod_query.group_by(OrderItem.product_name, OrderItem.sku, "category").order_by(text("revenue DESC")).limit(10).all()

        top_products = [
            {
                "name": r.product_name,
                "sku": r.sku or "N/A",
                "category": r.category,
                "units_sold": int(r.units_sold or 0),
                "revenue": round(float(r.revenue or 0), 2),
                "order_count": int(r.order_count or 0),
            }
            for r in top_prod_rows
        ]

        return {
            "by_category": categories,
            "by_platform": platforms,
            "top_products": top_products,
        }

    @staticmethod
    def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    # ---------------------------------------------------------------------------
    # Customer Analytics & Retention
    # ---------------------------------------------------------------------------

    def get_customer_analytics(
        self,
        date_range: str = "30d",
        source_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates customer growth, new vs returning customer rates,
        purchase frequency distribution, and customer lifetime value.
        """
        c_start, c_end, _, _ = self.resolve_date_range(date_range, start_date, end_date)

        total_customers = self.db.query(Customer).count()

        # Customer Order counts total
        cust_order_counts = (
            self.db.query(
                Customer.id,
                Customer.email,
                Customer.first_name,
                Customer.last_name,
                Customer.source_name,
                func.count(Order.id).label("total_orders"),
                func.coalesce(func.sum(Order.total_amount_usd), 0).label("ltv"),
                func.max(Order.order_date).label("last_order_date"),
                func.min(Order.order_date).label("first_order_date"),
            )
            .join(Order, Order.customer_id == Customer.id)
            .filter(~Order.status.in_(["cancelled", "refunded"]))
            .group_by(Customer.id, Customer.email, Customer.first_name, Customer.last_name, Customer.source_name)
            .all()
        )

        returning_customers = [c for c in cust_order_counts if c.total_orders > 1]
        single_order_customers = [c for c in cust_order_counts if c.total_orders == 1]
        repeat_rate = round((len(returning_customers) / len(cust_order_counts) * 100), 2) if cust_order_counts else 0.0

        # Frequency cohorts
        freq_cohorts = {
            "1_order": len(single_order_customers),
            "2_3_orders": len([c for c in cust_order_counts if 2 <= c.total_orders <= 3]),
            "4_5_orders": len([c for c in cust_order_counts if 4 <= c.total_orders <= 5]),
            "6_plus_orders": len([c for c in cust_order_counts if c.total_orders >= 6]),
        }

        # New vs returning in selected date range
        new_in_range = 0
        active_in_range = 0
        c_start_utc = self._to_utc(c_start)
        c_end_utc = self._to_utc(c_end)

        if c_start_utc:
            for c in cust_order_counts:
                last_dt = self._to_utc(c.last_order_date)
                first_dt = self._to_utc(c.first_order_date)

                if last_dt and last_dt >= c_start_utc:
                    if c_end_utc and last_dt > c_end_utc:
                        continue
                    active_in_range += 1
                    if first_dt and first_dt >= c_start_utc:
                        new_in_range += 1
        else:
            active_in_range = len(cust_order_counts)
            new_in_range = len(cust_order_counts)

        # Churn risk (inactive > 60 days)
        cutoff_60d = datetime.now(timezone.utc) - timedelta(days=60)
        churn_at_risk = [c for c in cust_order_counts if c.last_order_date and self._to_utc(c.last_order_date) < cutoff_60d]


        # Top Customers
        sorted_by_ltv = sorted(cust_order_counts, key=lambda x: float(x.ltv or 0), reverse=True)[:10]
        top_customers = [
            {
                "customer_id": str(c.id),
                "name": f"{c.first_name or ''} {c.last_name or ''}".strip() or "Anonymous",
                "email": c.email or "N/A",
                "source_name": c.source_name,
                "order_count": int(c.total_orders or 0),
                "lifetime_value": round(float(c.ltv or 0), 2),
                "last_order_date": c.last_order_date.isoformat() if c.last_order_date else None,
            }
            for c in sorted_by_ltv
        ]

        return {
            "summary": {
                "total_registered_customers": total_customers,
                "customers_with_orders": len(cust_order_counts),
                "active_in_period": active_in_range,
                "new_in_period": new_in_range,
                "repeat_customer_rate": repeat_rate,
                "churn_at_risk_count": len(churn_at_risk),
            },
            "frequency_cohorts": freq_cohorts,
            "top_customers": top_customers,
        }

    # ---------------------------------------------------------------------------
    # Business Anomaly & Alert Signals Engine
    # ---------------------------------------------------------------------------

    def get_business_alerts(
        self,
        date_range: str = "30d",
        source_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates thresholds and returns automated business alerts for the dashboard
        and AI Agent.
        """
        overview = self.get_overview_kpis(date_range, source_name, start_date, end_date)
        kpis = overview["kpis"]
        alerts = []

        # 1. Revenue change alert
        rev_pct = kpis["revenue"]["percentage_change"]
        if rev_pct is not None:
            if rev_pct <= -10.0:
                alerts.append({
                    "id": "alert_rev_drop",
                    "severity": "warning" if rev_pct > -25.0 else "danger",
                    "title": "Significant Revenue Decline",
                    "message": f"Revenue decreased by {abs(rev_pct)}% compared to the previous period.",
                    "metric": "revenue",
                    "change_pct": rev_pct,
                })
            elif rev_pct >= 15.0:
                alerts.append({
                    "id": "alert_rev_growth",
                    "severity": "success",
                    "title": "Strong Revenue Growth",
                    "message": f"Revenue grew by {rev_pct}% compared to the previous period.",
                    "metric": "revenue",
                    "change_pct": rev_pct,
                })

        # 2. Order Volume Alert
        ord_pct = kpis["orders"]["percentage_change"]
        if ord_pct is not None and ord_pct <= -15.0:
            alerts.append({
                "id": "alert_order_drop",
                "severity": "warning",
                "title": "Order Volume Decrease",
                "message": f"Total completed orders dropped by {abs(ord_pct)}%.",
                "metric": "orders",
                "change_pct": ord_pct,
            })

        # 3. Cancellation Rate Alert
        canc_info = kpis["cancellation_rate"]
        canc_rate = canc_info["current"]
        if canc_rate >= 5.0:
            alerts.append({
                "id": "alert_high_cancellation",
                "severity": "danger" if canc_rate >= 10.0 else "warning",
                "title": "High Order Cancellation / Refund Rate",
                "message": f"{canc_rate}% of order attempts were cancelled or refunded ({canc_info['cancelled_orders']} orders).",
                "metric": "cancellation_rate",
                "value": canc_rate,
            })

        # 4. Low Data / Empty State Info Alert
        if kpis["orders"]["current"] == 0:
            alerts.append({
                "id": "alert_no_orders",
                "severity": "info",
                "title": "No Sales Recorded",
                "message": "No valid order transactions were recorded during this selected date range.",
                "metric": "orders",
                "value": 0,
            })

        return alerts

    # ---------------------------------------------------------------------------
    # AI Agent Context Generator (For Person 3)
    # ---------------------------------------------------------------------------

    def get_ai_context(
        self,
        date_range: str = "30d",
        source_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Consolidates complete structured metrics, trends, breakdowns, and alerts
        into a clean, LLM-optimized payload for Person 3's AI Agent.
        """
        overview = self.get_overview_kpis(date_range, source_name, start_date, end_date)
        trends = self.get_revenue_trends(date_range, source_name, start_date, end_date)
        breakdown = self.get_sales_breakdown(date_range, source_name, start_date, end_date)
        customers = self.get_customer_analytics(date_range, source_name, start_date, end_date)
        alerts = self.get_business_alerts(date_range, source_name, start_date, end_date)

        return {
            "context_type": "business_analytics_snapshot",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "selected_period": overview["period"],
            "headline_kpis": overview["kpis"],
            "business_alerts": alerts,
            "sales_performance": {
                "top_products": breakdown["top_products"][:5],
                "top_categories": breakdown["by_category"][:5],
                "revenue_by_platform": breakdown["by_platform"],
            },
            "customer_health": {
                "repeat_customer_rate_pct": customers["summary"]["repeat_customer_rate"],
                "active_in_period": customers["summary"]["active_in_period"],
                "new_in_period": customers["summary"]["new_in_period"],
                "churn_at_risk_count": customers["summary"]["churn_at_risk_count"],
            },
            "daily_trend_summary": {
                "total_days_recorded": len(trends),
                "peak_revenue_day": max(trends, key=lambda x: x["revenue"]) if trends else None,
                "lowest_revenue_day": min(trends, key=lambda x: x["revenue"]) if trends else None,
            },
        }
