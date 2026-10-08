"""
Loader — persists ORM instances to PostgreSQL with deduplication.

Uses INSERT ... ON CONFLICT DO NOTHING (via merge) to prevent duplicate
records on re-runs. Returns counts of inserted vs duplicate records.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.data_quality_error import DataQualityError
from app.models.ingestion_run import IngestionRun
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.raw_record import RawRecord

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    inserted: int = 0
    duplicates: int = 0
    errors: int = 0


def upsert_customers(
    db: Session, customers: list[Customer]
) -> tuple[LoadResult, dict[str, uuid.UUID]]:
    """
    Upsert customers into the DB.
    Returns LoadResult and a map of external_id → internal UUID.
    """
    result = LoadResult()
    ext_to_id: dict[str, uuid.UUID] = {}

    for c in customers:
        # Check if already exists
        existing = (
            db.query(Customer)
            .filter_by(source_name=c.source_name, external_id=c.external_id)
            .first()
        )
        if existing:
            result.duplicates += 1
            ext_to_id[c.external_id] = existing.id
        else:
            db.add(c)
            db.flush()
            result.inserted += 1
            ext_to_id[c.external_id] = c.id

    return result, ext_to_id


def upsert_products(
    db: Session, products: list[Product]
) -> tuple[LoadResult, dict[str, uuid.UUID]]:
    """Upsert products; return LoadResult and external_id → internal UUID map."""
    result = LoadResult()
    ext_to_id: dict[str, uuid.UUID] = {}

    for p in products:
        existing = (
            db.query(Product)
            .filter_by(source_name=p.source_name, external_id=p.external_id)
            .first()
        )
        if existing:
            result.duplicates += 1
            for field in ("name", "sku", "category", "description", "unit_price", "currency", "stock_quantity", "reorder_point"):
                value = getattr(p, field)
                if value is not None:
                    setattr(existing, field, value)
            ext_to_id[p.external_id] = existing.id
        else:
            db.add(p)
            db.flush()
            result.inserted += 1
            ext_to_id[p.external_id] = p.id

    return result, ext_to_id


def upsert_orders(
    db: Session, orders: list[Order]
) -> tuple[LoadResult, list[uuid.UUID]]:
    """Upsert orders; return LoadResult and list of newly inserted order IDs."""
    result = LoadResult()
    new_ids: list[uuid.UUID] = []

    for o in orders:
        existing = (
            db.query(Order)
            .filter_by(source_name=o.source_name, external_id=o.external_id)
            .first()
        )
        if existing:
            result.duplicates += 1
        else:
            db.add(o)
            db.flush()
            result.inserted += 1
            new_ids.append(o.id)

    return result, new_ids


def insert_order_items(db: Session, items: list[OrderItem]) -> LoadResult:
    result = LoadResult()
    for item in items:
        db.add(item)
        result.inserted += 1
    db.flush()
    return result


def save_raw_records(
    db: Session,
    ingestion_run_id: uuid.UUID,
    data_source_id: uuid.UUID,
    record_type: str,
    records: list[dict],
) -> None:
    """Persist raw JSON payloads for debugging and reprocessing."""
    for raw in records:
        rr = RawRecord(
            ingestion_run_id=ingestion_run_id,
            data_source_id=data_source_id,
            record_type=record_type,
            raw_data=raw,
        )
        db.add(rr)
    db.flush()


def save_quality_errors(
    db: Session,
    ingestion_run_id: uuid.UUID,
    data_source_id: uuid.UUID,
    record_type: str,
    errors: list[dict],
) -> None:
    """Persist validation errors so failed records can be inspected."""
    for err in errors:
        raw = err.get("raw_data")
        # Convert non-serialisable types
        if raw:
            raw = {
                k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v)
                for k, v in raw.items()
            }
        dqe = DataQualityError(
            ingestion_run_id=ingestion_run_id,
            data_source_id=data_source_id,
            record_type=record_type,
            error_type=err.get("error_type", "unknown"),
            error_message=err.get("error_message", ""),
            raw_data=raw,
        )
        db.add(dqe)
    db.flush()
