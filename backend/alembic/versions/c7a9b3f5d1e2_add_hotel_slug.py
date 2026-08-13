"""add hotel slug

Revision ID: c7a9b3f5d1e2
Revises: 81c18eeee743
Create Date: 2026-08-11 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c7a9b3f5d1e2"
down_revision: str | None = "81c18eeee743"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("hotels", sa.Column("slug", sa.String(length=255), nullable=True))
    op.execute(
        """
        UPDATE hotels
        SET slug = lower(
            regexp_replace(
                regexp_replace(
                    translate(name, 'çğıöşüÇĞİÖŞÜ', 'cgiosucgiosu'),
                    '[^a-zA-Z0-9]+', '-', 'g'
                ),
                '^-+|-+$', '', 'g'
            )
        )
        WHERE slug IS NULL OR slug = ''
        """
    )
    op.execute(
        """
        UPDATE hotels SET slug = slug || '-' || id
        WHERE slug IN (
            SELECT slug FROM hotels GROUP BY slug HAVING count(*) > 1
        )
        """
    )
    op.alter_column("hotels", "slug", nullable=False)
    op.create_index("ix_hotels_slug", "hotels", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_hotels_slug", table_name="hotels")
    op.drop_column("hotels", "slug")
