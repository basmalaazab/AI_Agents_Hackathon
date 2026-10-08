"""
Data query endpoints — clean records for analytics and AI agent.

These endpoints provide read-only access to the cleaned business tables.
Intended for use by Person 2 (analytics/KPIs) and Person 3 (AI agent).
"""
import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app.models.customer import Customer
from app.models.data_quality_error import DataQualityError
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product

router = APIRouter(prefix="/data", tags=["data"], dependencies=[Depends(get_current_user)])


@router.get("/customers", summary="Sample of clean customer records")
def get_customers(
    limit: int = Query(default=20, le=200),
    source_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Customer)
    if source_name:
        q = q.filter_by(source_name=source_name)
    rows = q.limit(limit).all()
    return [_customer_dict(r) for r in rows]


@router.get("/orders", summary="Sample of clean order records")
def get_orders(
    limit: int = Query(default=20, le=200),
    source_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(Order)
    if source_name:
        q = q.filter_by(source_name=source_name)
    rows = q.order_by(Order.order_date.desc()).limit(limit).all()
    return [_order_dict(r) for r in rows]


@router.get("/products", summary="Sample of clean product records")
def get_products(
    limit: int = Query(default=50, le=500),
    db: Session = Depends(get_db),
):
    return [_product_dict(r) for r in db.query(Product).limit(limit).all()]


@router.get("/quality-errors", summary="Data quality errors from ingestion runs")
def get_quality_errors(
    run_id: uuid.UUID | None = Query(default=None),
    error_type: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(DataQualityError)
    if run_id:
        q = q.filter_by(ingestion_run_id=run_id)
    if error_type:
        q = q.filter_by(error_type=error_type)
    rows = q.order_by(DataQualityError.created_at.desc()).limit(limit).all()
    return [_dqe_dict(r) for r in rows]


@router.get("/analytics/revenue-summary", summary="Revenue KPIs for Person 2 analytics")
def revenue_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Provides pre-computed analytics metrics ready for the dashboard.
    All figures are in USD (total_amount_usd).
    """
    row = (
        db.query(
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(case((Order.currency == "USD", Order.total_amount_usd), else_=0)), 0).label("total_revenue_usd"),
            func.coalesce(func.avg(case((Order.currency == "USD", Order.total_amount_usd), else_=None)), 0).label("avg_order_value_usd"),
            func.count(func.distinct(Order.customer_id)).label("unique_customers"),
        )
        .filter(~Order.status.in_(["cancelled", "refunded"]))
        .one()
    )

    return {
        "total_orders": row.total_orders,
        "total_revenue_usd": float(row.total_revenue_usd),
        "avg_order_value_usd": float(row.avg_order_value_usd),
        "unique_customers_with_orders": row.unique_customers,
    }


@router.get("/analytics/sales-by-date", summary="Daily sales aggregates")
def sales_by_date(
    limit: int = Query(default=30, le=365),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            func.date(Order.order_date).label("sale_date"),
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(case((Order.currency == "USD", Order.total_amount_usd), else_=0)), 0).label("revenue_usd"),
        )
        .filter(~Order.status.in_(["cancelled", "refunded"]))
        .group_by(func.date(Order.order_date))
        .order_by(func.date(Order.order_date).desc())
        .limit(limit)
    )
    rows = query.all()
    return [
        {
            "sale_date": str(r.sale_date),
            "order_count": r.order_count,
            "revenue_usd": float(r.revenue_usd),
        }
        for r in rows
    ]


@router.get("/analytics/sales-by-product", summary="Sales aggregated by product")
def sales_by_product(
    limit: int = Query(default=20, le=200),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("total_units_sold"),
            func.coalesce(func.sum(case((OrderItem.currency == "USD", OrderItem.line_total), else_=0)), 0).label("total_revenue_usd"),
            func.count(func.distinct(OrderItem.order_id)).label("order_count"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .filter(~Order.status.in_(["cancelled", "refunded"]))
        .group_by(OrderItem.product_name)
        .order_by(func.coalesce(func.sum(case((OrderItem.currency == "USD", OrderItem.line_total), else_=0)), 0).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "product_name": r.product_name,
            "total_units_sold": int(r.total_units_sold or 0),
            "total_revenue_usd": float(r.total_revenue_usd or 0),
            "order_count": int(r.order_count or 0),
        }
        for r in rows
    ]


@router.get("/analytics/customer-frequency", summary="Customer purchase frequency")
def customer_frequency(
    limit: int = Query(default=20, le=200),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Customer.id.label("customer_id"),
            Customer.email,
            Customer.first_name,
            Customer.last_name,
            Customer.source_name,
            func.count(Order.id).label("order_count"),
            func.coalesce(func.sum(Order.total_amount_usd), 0).label("lifetime_value_usd"),
        )
        .join(Order, Order.customer_id == Customer.id)
        .filter(~Order.status.in_(["cancelled", "refunded"]))
        .group_by(Customer.id, Customer.email, Customer.first_name, Customer.last_name, Customer.source_name)
        .order_by(func.count(Order.id).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "customer_id": str(r.customer_id),
            "email": r.email,
            "first_name": r.first_name,
            "last_name": r.last_name,
            "source_name": r.source_name,
            "order_count": int(r.order_count or 0),
            "lifetime_value_usd": float(r.lifetime_value_usd or 0),
        }
        for r in rows
    ]


# ---- serialisation helpers -------------------------------------------------

def _customer_dict(c: Customer) -> dict:
    return {
        "id": str(c.id),
        "source_name": c.source_name,
        "external_id": c.external_id,
        "email": c.email,
        "first_name": c.first_name,
        "last_name": c.last_name,
        "city": c.city,
        "country": c.country,
    }


def _order_dict(o: Order) -> dict:
    return {
        "id": str(o.id),
        "source_name": o.source_name,
        "external_id": o.external_id,
        "customer_id": str(o.customer_id) if o.customer_id else None,
        "order_date": o.order_date.isoformat() if o.order_date else None,
        "status": o.status,
        "total_amount": float(o.total_amount),
        "currency": o.currency,
        "total_amount_usd": float(o.total_amount_usd) if o.total_amount_usd else None,
    }


def _product_dict(p: Product) -> dict:
    return {
        "id": str(p.id),
        "source_name": p.source_name,
        "external_id": p.external_id,
        "name": p.name,
        "sku": p.sku,
        "category": p.category,
        "unit_price": float(p.unit_price) if p.unit_price else None,
        "currency": p.currency,
    }


def _dqe_dict(e: DataQualityError) -> dict:
    return {
        "id": str(e.id),
        "ingestion_run_id": str(e.ingestion_run_id),
        "record_type": e.record_type,
        "error_type": e.error_type,
        "error_message": e.error_message,
        "raw_data": e.raw_data,
        "created_at": e.created_at.isoformat(),
    }
