import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking


class PaymentMethod(enum.StrEnum):
    """Payment channels accepted at checkout."""

    CARD = "card"  # Mock kredi karti (simulasyon)
    TRANSFER = "transfer"  # Havale / EFT


class PaymentStatus(enum.StrEnum):
    """Lifecycle states of a single payment attempt."""

    PENDING = "pending"  # Odeme baslatildi, bekleniyor
    PAID = "paid"  # Odendi, rezervasyon onaylandi
    FAILED = "failed"  # Simule odeme reddedildi
    REFUNDED = "refunded"  # Iade edildi


class Payment(Base, TimestampMixin):
    """Mock payment record linked to a booking."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Iliski
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), index=True
    )

    # Satis Detaylari
    amount: Mapped[float] = mapped_column(Numeric(10, 2))  # Odeme anindaki tutar
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, name="paymentmethod"))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="paymentstatus"),
        default=PaymentStatus.PENDING,
        index=True,
    )

    # Mock islem referansi (sanal "bank-prepis")
    transaction_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    booking: Mapped["Booking"] = relationship(back_populates="payments")
