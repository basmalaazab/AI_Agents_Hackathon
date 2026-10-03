"""
APScheduler-based lightweight scheduler.

Runs background pipeline jobs at a configurable interval.
This replaces Airflow for the MVP — Airflow DAG extension point is documented below.

AIRFLOW EXTENSION: To replace this with Airflow, create a DAG in dags/bi_ingestion_dag.py
that calls the /api/v1/pipelines/trigger endpoint or imports PipelineService directly.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_scheduled_pipelines() -> None:
    """Job executed by the scheduler on each tick."""
    from app.database import get_db_context
    from app.models.data_source import DataSource
    from app.services.pipeline_service import PipelineService

    logger.info("Scheduler: starting scheduled ingestion run.")
    with get_db_context() as db:
        service = PipelineService(db)
        sources = db.query(DataSource).filter_by(is_active=True).all()
        for source in sources:
            record_types = {
                "mock_api": ("customer", "product", "order"),
                "hubspot": ("customer", "product"),
                "stripe": ("customer", "product", "order"),
            }.get(source.source_type, ())
            for record_type in record_types:
                try:
                    run = service.trigger_source(
                        source_id=source.id,
                        record_type=record_type,
                        triggered_by="scheduler",
                    )
                    logger.info(
                        "Scheduler: run=%s source=%s type=%s status=%s",
                        run.id,
                        source.name,
                        record_type,
                        run.status,
                    )
                except Exception as exc:
                    logger.error(
                        "Scheduler: failed source=%s type=%s: %s",
                        source.name,
                        record_type,
                        exc,
                    )


def start_scheduler() -> None:
    global _scheduler
    settings = get_settings()
    interval = settings.scheduler_interval_minutes

    if interval <= 0:
        logger.info("Scheduler disabled (SCHEDULER_INTERVAL_MINUTES=0).")
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _run_scheduled_pipelines,
        trigger=IntervalTrigger(minutes=interval),
        id="bi_ingestion",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started: interval=%d minutes.", interval)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
