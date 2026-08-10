from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.base import Schema


class PaymentCreate(Schema):
    """A user-initiated payment attempt for an existing booking.

    ``method`` selects the channel; the amount is snapshotted server-side
    from the booking's fixed price (never trusted from the client).
    """

    booking_id: UUID = Field(..., description="Odeme yapilacak rezervasyonun ID'si")
    method: PaymentMethod = Field(
        ..., description="Odeme kanali: card (kart) veya transfer (havale)"
    )


class PaymentResponse(Schema):
    """Payment record returned to clients and the admin panel."""

    id: UUID
    booking_id: UUID
    amount: float
    method: PaymentMethod
    status: PaymentStatus
    transaction_id: str | None = None
    paid_at: datetime | None = None
    refunded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


PaymentRead = PaymentResponse
