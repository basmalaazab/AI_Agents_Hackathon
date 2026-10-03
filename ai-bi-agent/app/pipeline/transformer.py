"""
Transformer — converts cleaned DataFrames into SQLAlchemy model instances.

Handles cross-source identity, linking orders to customers/products, and
ensuring that (source_name, external_id) is the idempotency key used at
database load time.
"""
from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Any

import pandas as pd

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product

logger = logging.getLogger(__name__)


def transform_customers(
    df: pd.DataFrame, source_name: str
) -> list[Customer]:
    """Convert a cleaned customers DataFrame into Customer ORM instances."""
    customers: list[Customer] = []
    for _, row in df.iterrows():
        c = Customer(
            source_name=source_name,
            external_id=str(row["customer_id"]),
            email=_get(row, "email"),
            first_name=_get(row, "first_name"),
            last_name=_get(row, "last_name"),
            phone=_get(row, "phone"),
            city=_get(row, "city"),
            country=_get(row, "country"),
        )
        customers.append(c)
    return customers


def transform_products(
    df: pd.DataFrame, source_name: str
) -> list[Product]:
    """Convert a cleaned products DataFrame into Product ORM instances."""
    products: list[Product] = []
    for _, row in df.iterrows():
        p = Product(
            source_name=source_name,
            external_id=str(row["product_id"]),
            name=str(row["product_name"]),
            sku=_get(row, "sku"),
            category=_get(row, "category"),
            description=_get(row, "description"),
            unit_price=_decimal(row, "unit_price"),
            currency=row.get("currency", "USD") or "USD",
        )
        products.append(p)
    return products


def transform_orders(
    df: pd.DataFrame,
    source_name: str,
    customer_map: dict[str, uuid.UUID] | None = None,
) -> list[Order]:
    """
    Convert a cleaned orders DataFrame into Order ORM instances.

    customer_map: maps external_customer_id → internal Customer.id
    """
    orders: list[Order] = []
    for _, row in df.iterrows():
        cust_ext_id = _get(row, "customer_id")
        cust_internal_id = (
            customer_map.get(cust_ext_id) if (customer_map and cust_ext_id) else None
        )

        order_date = row.get("order_date")
        if hasattr(order_date, "to_pydatetime"):
            order_date = order_date.to_pydatetime()

        o = Order(
            source_name=source_name,
            external_id=str(row["order_id"]),
            customer_id=cust_internal_id,
            order_date=order_date,
            status=str(row.get("status", "completed")),
            total_amount=_decimal(row, "total_amount") or Decimal("0"),
            currency=row.get("currency", "USD") or "USD",
            total_amount_usd=_decimal(row, "total_amount_usd"),
        )
        orders.append(o)
    return orders


def transform_order_items(
    df: pd.DataFrame,
    order_id: uuid.UUID,
) -> list[OrderItem]:
    """
    Build OrderItem instances for a single order row.
    Used when the CSV contains per-item columns (product_name, quantity, unit_price).
    """
    items: list[OrderItem] = []

    if "product_name" not in df.columns:
        return items

    for _, row in df.iterrows():
        qty = _int(row, "quantity", default=1)
        unit_price = _decimal(row, "unit_price") or Decimal("0")
        line_total = _decimal(row, "line_total") or (unit_price * qty)

        item = OrderItem(
            order_id=order_id,
            product_name=str(row.get("product_name", "Unknown")),
            sku=_get(row, "sku"),
            quantity=qty,
            unit_price=unit_price,
            line_total=line_total,
            currency=row.get("currency", "USD") or "USD",
        )
        items.append(item)
    return items


# ---- helpers ---------------------------------------------------------------

def _get(row: pd.Series, col: str) -> str | None:
    val = row.get(col)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def _decimal(row: pd.Series, col: str) -> Decimal | None:
    val = row.get(col)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


def _int(row: pd.Series, col: str, default: int = 0) -> int:
    val = row.get(col)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return default
