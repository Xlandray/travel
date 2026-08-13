import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.models.audit_log import AuditAction
from app.schemas.base import Schema


class AuditLogRead(Schema):
    """One line of the trail. Read-only — there is no create or update DTO."""

    id: uuid.UUID
    recorded_at: datetime
    action: AuditAction
    actor_id: uuid.UUID | None
    actor_email: str | None
    actor_is_superuser: bool | None
    booking_id: uuid.UUID | None
    payment_id: uuid.UUID | None
    amount: Decimal | None
    detail: dict[str, Any] | None
