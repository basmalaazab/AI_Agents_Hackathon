"""DataQualityError — records validation failures without discarding raw data."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DataQualityError(Base):
    __tablename__ = "data_quality_errors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingestion_runs.id"), nullable=False
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False
    )
    record_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # order | customer | product
    error_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # missing_field | invalid_type | duplicate | etc.
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    ingestion_run = relationship("IngestionRun", back_populates="quality_errors")

    __table_args__ = (
        Index("ix_dqe_run_id", "ingestion_run_id"),
        Index("ix_dqe_source_id", "data_source_id"),
        Index("ix_dqe_error_type", "error_type"),
    )

    def __repr__(self) -> str:
        return f"<DataQualityError type={self.error_type!r} msg={self.error_message[:60]!r}>"
