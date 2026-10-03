"""IngestionRun — tracks each pipeline execution."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"     # some records failed validation
    FAILED = "failed"


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=RunStatus.PENDING, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    records_valid: Mapped[int] = mapped_column(Integer, default=0)
    records_invalid: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[str] = mapped_column(
        String(50), default="manual"
    )  # manual | scheduler | api

    # Relationships
    data_source = relationship("DataSource", back_populates="ingestion_runs")
    raw_records = relationship(
        "RawRecord", back_populates="ingestion_run", cascade="all, delete-orphan"
    )
    quality_errors = relationship(
        "DataQualityError",
        back_populates="ingestion_run",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<IngestionRun id={self.id} status={self.status!r}>"
