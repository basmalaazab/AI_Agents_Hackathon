"""RawRecord — preserves original ingested data as JSON for debugging/reprocessing."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RawRecord(Base):
    __tablename__ = "raw_records"

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
    raw_data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    ingestion_run = relationship("IngestionRun", back_populates="raw_records")

    __table_args__ = (
        Index("ix_raw_records_run_id", "ingestion_run_id"),
        Index("ix_raw_records_source_id", "data_source_id"),
        Index("ix_raw_records_type", "record_type"),
    )

    def __repr__(self) -> str:
        return f"<RawRecord id={self.id} type={self.record_type!r}>"
