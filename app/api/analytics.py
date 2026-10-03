"""
Analytics API endpoints — Exposes business intelligence data for Dashboard & AI Agent.
"""
import io
import csv
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", summary="Executive KPI summary & period-over-period comparison")
def get_overview(
    date_range: str = Query(default="30d", description="Preset: today, 7d, 30d, 3m, 6m, 12m, all, custom"),
    source_name: Optional[str] = Query(default=None, description="Filter by data source platform"),
    start_date: Optional[str] = Query(default=None, description="ISO start date if date_range=custom"),
    end_date: Optional[str] = Query(default=None, description="ISO end date if date_range=custom"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    svc = AnalyticsService(db)
    return svc.get_overview_kpis(date_range, source_name, start_date, end_date)


@router.get("/revenue-trends", summary="Daily/Periodic time-series revenue & order volume")
def get_revenue_trends(
    date_range: str = Query(default="30d"),
    source_name: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db)
    return svc.get_revenue_trends(date_range, source_name, start_date, end_date)


@router.get("/sales-breakdown", summary="Sales breakdown by product category, platform, and top products")
def get_sales_breakdown(
    date_range: str = Query(default="30d"),
    source_name: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db)
    return svc.get_sales_breakdown(date_range, source_name, start_date, end_date)


@router.get("/customers", summary="Customer growth, retention cohorts, LTV, and churn indicators")
def get_customer_analytics(
    date_range: str = Query(default="30d"),
    source_name: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db)
    return svc.get_customer_analytics(date_range, source_name, start_date, end_date)


@router.get("/alerts", summary="Automated business anomaly signals & performance indicators")
def get_business_alerts(
    date_range: str = Query(default="30d"),
    source_name: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db)
    return svc.get_business_alerts(date_range, source_name, start_date, end_date)


@router.get("/ai-context", summary="Structured analytics payload formatted for Person 3 AI Agent")
def get_ai_context(
    date_range: str = Query(default="30d"),
    source_name: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Returns a unified JSON data package designed for Person 3's AI Agent
    to consume for natural language reasoning, anomaly analysis, and recommendation generation.
    """
    svc = AnalyticsService(db)
    return svc.get_ai_context(date_range, source_name, start_date, end_date)


@router.get("/export/csv", summary="Download aggregated business analytics report as CSV")
def export_csv_report(
    date_range: str = Query(default="30d"),
    source_name: Optional[str] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    svc = AnalyticsService(db)
    trends = svc.get_revenue_trends(date_range, source_name, start_date, end_date)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Revenue (USD)", "Completed Orders", "Average Order Value (USD)"])

    for r in trends:
        writer.writerow([r["date"], r["revenue"], r["orders"], r["avg_order_value"]])

    output.seek(0)
    filename = f"analytics_report_{date_range}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
