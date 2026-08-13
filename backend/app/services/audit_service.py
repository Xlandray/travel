import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.audit_log import AuditAction, AuditLog


def record(
    db: AsyncSession,
    action: AuditAction,
    *,
    actor: User | None,
    booking_id: uuid.UUID | None = None,
    payment_id: uuid.UUID | None = None,
    amount: Decimal | float | None = None,
    detail: dict[str, Any] | None = None,
) -> AuditLog:
    """Add an audit entry to the caller's session. Does not commit.

    Not committing is the point. The entry rides along with the change it
    describes, so the two land together or not at all: a rolled-back refund
    leaves no line claiming it happened, and a refund cannot be committed with
    its line missing. Writing the log in its own transaction — or after the
    business commit — would break one of those halves depending on which side
    failed.

    The actor's email is copied in rather than joined to later, so the entry
    still says who did it after the account is renamed or deleted.
    """
    entry = AuditLog(
        action=action,
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else None,
        actor_is_superuser=actor.is_superuser if actor else None,
        booking_id=booking_id,
        payment_id=payment_id,
        amount=Decimal(str(amount)) if amount is not None else None,
        detail=detail,
    )
    db.add(entry)
    return entry


def list_entries(
    *,
    action: AuditAction | None = None,
    booking_id: uuid.UUID | None = None,
    payment_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
) -> Select[tuple[AuditLog]]:
    """The filtered query, newest first. Kept here so the count and the page agree."""
    stmt = select(AuditLog)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if booking_id is not None:
        stmt = stmt.where(AuditLog.booking_id == booking_id)
    if payment_id is not None:
        stmt = stmt.where(AuditLog.payment_id == payment_id)
    if actor_id is not None:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    return stmt.order_by(AuditLog.seq.desc())
