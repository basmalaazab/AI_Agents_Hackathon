"""DataSource model — tracks configured ingestion sources."""
import uuid
import re
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # csv | mock_api | google_sheets | shopify
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON blob — no credentials stored here
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    ingestion_runs = relationship(
        "IngestionRun", back_populates="data_source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DataSource id={self.id} name={self.name!r} type={self.source_type!r}>"


def make_workspace_source_key(workspace_id: uuid.UUID, display_name: str) -> str:
    """Keep source identities globally unique while showing a human label in the UI."""
    slug = re.sub(r"[^a-z0-9]+", "_", display_name.strip().lower()).strip("_") or "source"
    return f"ws_{workspace_id.hex}_{slug[:80]}"
