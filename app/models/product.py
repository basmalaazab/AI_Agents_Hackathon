"""Product model."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    order_items = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        UniqueConstraint("source_name", "external_id", name="uq_product_source_ext_id"),
        Index("ix_product_source_name", "source_name"),
        Index("ix_product_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r}>"
