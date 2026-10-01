"""Data sources CRUD endpoints."""
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.data_source import DataSource

router = APIRouter(prefix="/sources", tags=["data-sources"])


class DataSourceCreate(BaseModel):
    name: str
    source_type: str  # csv | mock_api | spreadsheet
    description: str | None = None
    is_active: bool = True


class DataSourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_type: str
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=list[DataSourceResponse], summary="List all data sources")
def list_sources(db: Session = Depends(get_db)):
    return db.query(DataSource).all()


@router.post(
    "",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new data source",
)
def create_source(payload: DataSourceCreate, db: Session = Depends(get_db)):
    existing = db.query(DataSource).filter_by(name=payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A data source with name '{payload.name}' already exists.",
        )
    source = DataSource(
        name=payload.name,
        source_type=payload.source_type,
        description=payload.description,
        is_active=payload.is_active,
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


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: uuid.UUID, db: Session = Depends(get_db)):
    source = db.query(DataSource).filter_by(id=source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")
    db.delete(source)
    db.commit()
