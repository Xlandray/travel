"""add audit logs

An append-only trail of who moved money or seats. Deliberately has no foreign
keys: the record has to outlive the booking, payment and account it describes
(see `app/models/audit_log.py`).

Revision ID: e5c2f9a41b60
Revises: d4b1c8e07a35
Create Date: 2026-08-13

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e5c2f9a41b60"
down_revision: str | None = "d4b1c8e07a35"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

AUDIT_ACTIONS = (
    "BOOKING_CREATED",
    "BOOKING_CANCELLED",
    "BOOKING_CONFIRMED",
    "BOOKING_EXPIRED",
    "PAYMENT_OPENED",
    "PAYMENT_PAID",
    "PAYMENT_REFUNDED",
)


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("seq", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.Enum(*AUDIT_ACTIONS, name="auditaction"),
            nullable=False,
        ),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=True),
        sa.Column("actor_is_superuser", sa.Boolean(), nullable=True),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("seq"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_seq", "audit_logs", [sa.text("seq DESC")])
    op.create_index("ix_audit_logs_booking_id", "audit_logs", ["booking_id"])
    op.create_index("ix_audit_logs_payment_id", "audit_logs", ["payment_id"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_payment_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_booking_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_seq", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")
    sa.Enum(name="auditaction").drop(op.get_bind())
