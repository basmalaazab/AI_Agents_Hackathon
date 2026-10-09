"""
Ingestion Service — orchestrates the full data pipeline for a single run.

Pipeline stages:
1. Fetch raw records from connector
2. Store raw records
3. Validate records → split into valid / invalid
4. Record data quality errors for invalid records
5. Clean valid records
6. Deduplicate within batch
7. Transform to ORM instances
8. Load into clean tables (upsert / skip duplicates)
9. Update IngestionRun status and counters
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.connectors.base import BaseConnector
from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun, RunStatus
from app.models.order import Order
from app.pipeline import cleaner, loader, transformer
from app.pipeline.validator import (
    ValidationResult,
    validate_customers,
    validate_orders,
    validate_products,
)

logger = logging.getLogger(__name__)


class IngestionService:
    """Runs the full ingestion pipeline for one (data_source, record_type) combination."""

    def __init__(self, db):
        self.db = db

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_csv_ingestion(
        self,
        data_source: DataSource,
        record_type: str,
        file_content: bytes,
        triggered_by: str = "api",
    ) -> IngestionRun:
        from app.connectors.csv_connector import CSVConnector

        connector = CSVConnector(source_name=data_source.name)
        raw_records = connector.fetch(record_type=record_type, file_content=file_content)
        return self._run_pipeline(data_source, record_type, raw_records, triggered_by)

    def run_api_ingestion(
        self,
        data_source: DataSource,
        record_type: str,
        connector: BaseConnector,
        since: str | None = None,
        triggered_by: str = "scheduler",
    ) -> IngestionRun:
        try:
            raw_records = connector.fetch(record_type=record_type, since=since)
        except Exception as exc:
            run = self._create_run(data_source.id, triggered_by)
            self._finish_run(run, RunStatus.FAILED, error_message=str(exc))
            self.db.commit()
            logger.exception(
                "Connector fetch failed for source=%s type=%s",
                data_source.name,
                record_type,
            )
            return run
        return self._run_pipeline(data_source, record_type, raw_records, triggered_by)

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    def _run_pipeline(
        self,
        data_source: DataSource,
        record_type: str,
        raw_records: list[dict],
        triggered_by: str,
    ) -> IngestionRun:
        run = self._create_run(data_source.id, triggered_by)

        try:
            run.records_fetched = len(raw_records)

            # 1. Save raw records for auditability
            loader.save_raw_records(
                self.db,
                ingestion_run_id=run.id,
                data_source_id=data_source.id,
                record_type=record_type,
                records=raw_records,
            )

            # 2. Validate
            df = pd.DataFrame(raw_records)
            validation = self._validate(df, record_type)
            run.records_valid = validation.valid_count
            run.records_invalid = validation.error_count

            # 3. Persist quality errors
            if validation.errors:
                loader.save_quality_errors(
                    self.db,
                    ingestion_run_id=run.id,
                    data_source_id=data_source.id,
                    record_type=record_type,
                    errors=validation.errors,
                )
                logger.warning(
                    "Run %s: %d record(s) failed validation for source=%s type=%s",
                    run.id,
                    validation.error_count,
                    data_source.name,
                    record_type,
                )

            if validation.valid_rows.empty:
                self._finish_run(run, RunStatus.PARTIAL if validation.errors else RunStatus.SUCCESS)
                return run

            # 4. Clean
            cleaned_df = self._clean(validation.valid_rows, record_type)

            # 5. Intra-batch deduplication
            id_col = self._id_column(record_type)
            if record_type == "order":
                # Order CSVs may have one row per line item. Keep all rows so
                # product analytics retain every item; parent orders are
                # deduplicated inside _transform_and_load below.
                dup_count = 0
            else:
                cleaned_df, dup_count = cleaner.deduplicate_by_column(cleaned_df, id_col)
            run.records_duplicate += dup_count

            # 6. Transform + Load
            inserted, db_dups = self._transform_and_load(
                cleaned_df, record_type, data_source.name
            )
            run.records_inserted = inserted
            run.records_duplicate += db_dups

            status = RunStatus.PARTIAL if validation.errors else RunStatus.SUCCESS
            self._finish_run(run, status)

        except Exception as exc:
            logger.exception("Pipeline failed for run %s: %s", run.id, exc)
            try:
                self.db.rollback()
            except Exception:
                pass
            # Persist just the failure status in a new transaction
            try:
                from app.models.ingestion_run import IngestionRun as IRun
                fail_run = self.db.query(IRun).filter_by(id=run.id).first()
                if fail_run:
                    self._finish_run(fail_run, RunStatus.FAILED, error_message=str(exc))
                    self.db.commit()
            except Exception as inner:
                logger.error("Could not update run status after failure: %s", inner)
            return run


        self.db.commit()
        return run

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_run(self, source_id: uuid.UUID, triggered_by: str) -> IngestionRun:
        run = IngestionRun(
            data_source_id=source_id,
            status=RunStatus.RUNNING,
            triggered_by=triggered_by,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def _finish_run(
        self,
        run: IngestionRun,
        status: RunStatus,
        error_message: str | None = None,
    ) -> None:
        run.status = status
        run.finished_at = datetime.now(timezone.utc)
        if error_message:
            run.error_message = error_message[:2000]

    def _validate(self, df: pd.DataFrame, record_type: str) -> ValidationResult:
        validators = {
            "order": validate_orders,
            "customer": validate_customers,
            "product": validate_products,
        }
        fn = validators.get(record_type)
        if fn is None:
            raise ValueError(f"No validator for record_type={record_type!r}")
        return fn(df)

    def _clean(self, df: pd.DataFrame, record_type: str) -> pd.DataFrame:
        cleaners = {
            "order": cleaner.clean_orders,
            "customer": cleaner.clean_customers,
            "product": cleaner.clean_products,
        }
        fn = cleaners.get(record_type)
        if fn is None:
            raise ValueError(f"No cleaner for record_type={record_type!r}")
        return fn(df)

    def _id_column(self, record_type: str) -> str:
        return {
            "order": "order_id",
            "customer": "customer_id",
            "product": "product_id",
        }[record_type]

    def _transform_and_load(
        self,
        df: pd.DataFrame,
        record_type: str,
        source_name: str,
    ) -> tuple[int, int]:
        """Returns (inserted, duplicates)."""
        if record_type == "customer":
            instances = transformer.transform_customers(df, source_name)
            result, _ = loader.upsert_customers(self.db, instances)
            return result.inserted, result.duplicates

        if record_type == "product":
            instances = transformer.transform_products(df, source_name)
            result, _ = loader.upsert_products(self.db, instances)
            return result.inserted, result.duplicates

        if record_type == "order":
            # Try to resolve customer IDs from this session
            from app.models.customer import Customer

            customer_map: dict[str, uuid.UUID] = {}
            order_rows = df.drop_duplicates(subset=["order_id"], keep="first")
            if "customer_id" in order_rows.columns:
                ext_ids = order_rows["customer_id"].dropna().astype(str).unique().tolist()
                rows = (
                    self.db.query(Customer.external_id, Customer.id)
                    .filter(
                        Customer.source_name == source_name,
                        Customer.external_id.in_(ext_ids),
                    )
                    .all()
                )
                customer_map = {r.external_id: r.id for r in rows}

            instances = transformer.transform_orders(order_rows, source_name, customer_map)
            result, _ = loader.upsert_orders(self.db, instances)
            external_ids = [order.external_id for order in instances]
            persisted_orders = (
                self.db.query(Order.external_id, Order.id)
                .filter(
                    Order.source_name == source_name,
                    Order.external_id.in_(external_ids),
                )
                .all()
            )
            order_ids_by_external_id = {row.external_id: row.id for row in persisted_orders}

            from app.models.order_item import OrderItem

            orders_with_items = {
                row.order_id
                for row in (
                    self.db.query(OrderItem.order_id)
                    .filter(OrderItem.order_id.in_(list(order_ids_by_external_id.values())))
                    .distinct()
                    .all()
                )
            }
            order_items = []
            for _, row in df.iterrows():
                external_id = str(row.get("order_id", "")).strip()
                order_id = order_ids_by_external_id.get(external_id)
                if order_id is not None and order_id not in orders_with_items:
                    order_items.extend(
                        transformer.transform_order_items(
                            pd.DataFrame([row]), order_id
                        )
                    )
            if order_items:
                loader.insert_order_items(self.db, order_items)

            return result.inserted, result.duplicates

        raise ValueError(f"Unknown record_type={record_type!r}")
