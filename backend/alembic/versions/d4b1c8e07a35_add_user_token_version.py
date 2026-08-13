"""add user token version

Gives every account a counter that access tokens are stamped with, so issued
tokens can be recalled (see `User.token_version`).

Revision ID: d4b1c8e07a35
Revises: c7a9b3f5d1e2
Create Date: 2026-08-13

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d4b1c8e07a35"
down_revision: str | None = "c7a9b3f5d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
