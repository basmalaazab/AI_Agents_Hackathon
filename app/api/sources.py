"""Data sources CRUD endpoints."""
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user, require_manager
from app.models.data_source import DataSource, make_workspace_source_key
from app.config import get_settings

router = APIRouter(prefix="/sources", tags=["data-sources"], dependencies=[Depends(get_current_user)])


class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    source_type: Literal["csv", "mock_api", "spreadsheet", "hubspot", "stripe"]
    description: str | None = None
    is_active: bool = True


class DataSourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None = None
    source_type: str
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=list[DataSourceResponse], summary="List all data sources")
def list_sources(db: Session = Depends(get_db)):
    return db.query(DataSource).all()


@router.get("/integration-readiness")
def integration_readiness():
    settings = get_settings()
    return {"stripe": {"configured": bool(settings.stripe_secret_key),
                        "message": "Stripe test/live secret is configured on the backend." if settings.stripe_secret_key else "Set STRIPE_SECRET_KEY in the backend environment to enable live sync."}}


@router.post(
    "",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new data source",
    dependencies=[Depends(require_manager)],
)
def create_source(payload: DataSourceCreate, db: Session = Depends(get_db)):
    display_name = payload.name.strip()
    internal_name = make_workspace_source_key(db.info["workspace_id"], display_name)
    existing = db.query(DataSource).filter_by(name=internal_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A data source named '{display_name}' already exists in this company.",
        )
    source = DataSource(
        name=internal_name,
        display_name=display_name,
        source_type=payload.source_type,
        description=payload.description,
        is_active=payload.is_active,
        workspace_id=db.info["workspace_id"],
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/{source_id}", response_model=DataSourceResponse, summary="Get a data source")
def get_source(source_id: uuid.UUID, db: Session = Depends(get_db)):
    source = db.query(DataSource).filter_by(id=source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_manager)])
def delete_source(source_id: uuid.UUID, db: Session = Depends(get_db)):
    source = db.query(DataSource).filter_by(id=source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")
    db.delete(source)
    db.commit()
