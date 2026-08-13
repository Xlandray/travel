import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Identity, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditAction(enum.StrEnum):
    """What happened. One value per event worth being able to look up later."""

    BOOKING_CREATED = "booking.created"
    BOOKING_CANCELLED = "booking.cancelled"
    BOOKING_CONFIRMED = "booking.confirmed"
    BOOKING_EXPIRED = "booking.expired"
    PAYMENT_OPENED = "payment.opened"
    PAYMENT_PAID = "payment.paid"
    PAYMENT_REFUNDED = "payment.refunded"


class AuditLog(Base):
    """An append-only record of who moved money or seats, and when.

    Nothing here is a foreign key, on purpose. A payment row is deleted with
    its booking (`ON DELETE CASCADE`), and an account can be removed; if the
    trail were wired up the same way, the record of a refund would disappear
    along with the thing it describes — exactly when somebody would want to
    read it. The ids are kept as plain columns and the actor's email is
    snapshotted at write time, so an entry stays legible after everything it
    refers to is gone.

    There is no update path and no delete endpoint. Entries are written by
    `audit_service.record`, which only adds to the caller's session: the entry
    is committed by the same transaction as the change it describes, so the log
    cannot claim something that was rolled back, and a change cannot commit
    without its entry.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # The order entries were written in, and the only thing worth sorting on.
    # Timestamps cannot do this job: several entries are written inside one
    # transaction — paying records the charge and the confirmation together —
    # and the tie has to break the same way every time it is read.
    seq: Mapped[int] = mapped_column(BigInteger, Identity(always=True), unique=True)
    # `clock_timestamp()`, not `CURRENT_TIMESTAMP`: the latter is the moment the
    # transaction began, so entries written seconds apart inside a long one
    # would all claim the same time.
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("clock_timestamp()")
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="auditaction"), index=True)

    # Null actor means the system did it — today only the expiry sweeper, which
    # runs on a timer with nobody behind it.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_is_superuser: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    booking_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # The sum involved, snapshotted. Reading it back off the payment would give
    # today's value, not the one that moved.
    amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Whatever else makes the line readable on its own: seat counts, the status
    # it moved from and to, the transaction reference.
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        # The log is read newest-first, and filtered by the thing you are
        # investigating: a booking, a payment, or a person.
        Index("ix_audit_logs_seq", seq.desc()),
        Index("ix_audit_logs_booking_id", "booking_id"),
        Index("ix_audit_logs_payment_id", "payment_id"),
        Index("ix_audit_logs_actor_id", "actor_id"),
    )
