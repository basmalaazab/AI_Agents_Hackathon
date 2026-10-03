"""
Pipeline service — higher-level operations for triggering and monitoring pipelines.
Used by API routes and the scheduler.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.connectors import get_connector
from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)


class PipelineService:

    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService(db)

    def trigger_source(
        self,
        source_id: uuid.UUID,
        record_type: str,
        triggered_by: str = "api",
        since: str | None = None,
    ) -> IngestionRun:
        """Trigger a pipeline run for an existing DataSource by its ID."""
        source = self.db.query(DataSource).filter_by(id=source_id).first()
        if source is None:
            raise ValueError(f"DataSource with id={source_id} not found.")
        if not source.is_active:
            raise ValueError(f"DataSource '{source.name}' is not active.")

        connector = get_connector(
            source_type=source.source_type,
            source_name=source.name,
        )
        return self.ingestion.run_api_ingestion(
            data_source=source,
            record_type=record_type,
            connector=connector,
            since=since,
            triggered_by=triggered_by,
        )

    def get_run(self, run_id: uuid.UUID) -> IngestionRun | None:
        return self.db.query(IngestionRun).filter_by(id=run_id).first()

    def list_runs(
        self,
        source_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[IngestionRun]:
        q = self.db.query(IngestionRun)
        if source_id:
            q = q.filter_by(data_source_id=source_id)
        return q.order_by(IngestionRun.started_at.desc()).limit(limit).all()

    def get_summary(self) -> dict[str, Any]:
        """Return aggregate ingestion statistics."""
        from sqlalchemy import func
        from app.models.data_quality_error import DataQualityError
        from app.models.customer import Customer
        from app.models.order import Order
        from app.models.product import Product

        total_runs = self.db.query(func.count(IngestionRun.id)).scalar() or 0
        total_errors = self.db.query(func.count(DataQualityError.id)).scalar() or 0
        total_customers = self.db.query(func.count(Customer.id)).scalar() or 0
        total_orders = self.db.query(func.count(Order.id)).scalar() or 0
        total_products = self.db.query(func.count(Product.id)).scalar() or 0

        return {
            "total_runs": total_runs,
            "total_quality_errors": total_errors,
            "total_customers": total_customers,
            "total_orders": total_orders,
            "total_products": total_products,
        }
