"""Pipeline management endpoints."""
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

ALLOWED_RECORD_TYPES = {"order", "customer", "product"}


class TriggerRequest(BaseModel):
    source_id: uuid.UUID
    record_type: str
    since: str | None = None  # ISO datetime for incremental ingestion


class RunResponse(BaseModel):
    id: uuid.UUID
    data_source_id: uuid.UUID
    status: str
    started_at: datetime
    finished_at: datetime | None
    records_fetched: int
    records_valid: int
    records_invalid: int
    records_inserted: int
    records_duplicate: int
    triggered_by: str
    error_message: str | None

    model_config = {"from_attributes": True}


@router.post("/trigger", response_model=RunResponse, summary="Trigger a pipeline run")
def trigger_pipeline(payload: TriggerRequest, db: Session = Depends(get_db)):
    if payload.record_type not in ALLOWED_RECORD_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"record_type must be one of {sorted(ALLOWED_RECORD_TYPES)}.",
        )
    svc = PipelineService(db)
    try:
        run = svc.trigger_source(
            source_id=payload.source_id,
            record_type=payload.record_type,
            since=payload.since,
            triggered_by="api",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return run


@router.get("/runs/{run_id}", response_model=RunResponse, summary="Get pipeline run status")
def get_run(run_id: uuid.UUID, db: Session = Depends(get_db)):
    svc = PipelineService(db)
    run = svc.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion run not found.")
    return run


@router.get("/runs", response_model=list[RunResponse], summary="List ingestion history")
def list_runs(
    source_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    svc = PipelineService(db)
    return svc.list_runs(source_id=source_id, limit=limit)


@router.get("/summary", summary="Ingestion and data-quality summary")
def get_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    svc = PipelineService(db)
    return svc.get_summary()
