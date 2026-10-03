"""Order model."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )

    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="completed", nullable=False
    )  # pending | completed | cancelled | refunded

    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Normalized to USD for cross-currency analytics
    total_amount_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source_name", "external_id", name="uq_order_source_ext_id"),
        Index("ix_order_order_date", "order_date"),
        Index("ix_order_source_name", "source_name"),
        Index("ix_order_customer_id", "customer_id"),
        Index("ix_order_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} ext={self.external_id!r} total={self.total_amount}>"
