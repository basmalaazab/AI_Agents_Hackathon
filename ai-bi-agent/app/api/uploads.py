"""CSV upload endpoints."""
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/upload", tags=["uploads"])

ALLOWED_RECORD_TYPES = {"order", "customer", "product"}


class UploadResponse(BaseModel):
    run_id: uuid.UUID
    source_name: str
    record_type: str
    status: str
    records_fetched: int
    records_valid: int
    records_invalid: int
    records_inserted: int
    records_duplicate: int
    error_message: str | None


@router.post(
    "/csv",
    response_model=UploadResponse,
    summary="Upload a CSV file and trigger ingestion",
    description=(
        "Upload a CSV file containing business records. "
        "Specify `record_type` as one of: order, customer, product. "
        "If `source_name` is not registered, it is created automatically."
    ),
)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file to upload"),
    record_type: str = Form(..., description="Type of records: order | customer | product"),
    source_name: str = Form(..., description="Logical name for this data source"),
    db: Session = Depends(get_db),
):
    if record_type not in ALLOWED_RECORD_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"record_type must be one of {sorted(ALLOWED_RECORD_TYPES)}.",
        )

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .csv files are accepted.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    # Get or create data source
    source = db.query(DataSource).filter_by(name=source_name).first()
    if source is None:
        source = DataSource(name=source_name, source_type="csv")
        db.add(source)
        db.flush()

    svc = IngestionService(db)
    run: IngestionRun = svc.run_csv_ingestion(
        data_source=source,
        record_type=record_type,
        file_content=content,
        triggered_by="api",
    )

    return UploadResponse(
        run_id=run.id,
        source_name=source_name,
        record_type=record_type,
        status=run.status,
        records_fetched=run.records_fetched,
        records_valid=run.records_valid,
        records_invalid=run.records_invalid,
        records_inserted=run.records_inserted,
        records_duplicate=run.records_duplicate,
        error_message=run.error_message,
    )
