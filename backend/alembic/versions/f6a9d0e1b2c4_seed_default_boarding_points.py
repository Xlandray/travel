"""seed_default_boarding_points

Revision ID: f6a9d0e1b2c4
Revises: b5455f844a1e
Create Date: 2026-08-10 10:14:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f6a9d0e1b2c4"
down_revision: str | None = "b5455f844a1e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_BOARDING_POINTS = (
    ("33333333-3333-3333-3333-333333333333", "Çorlu Merkez", "Heykel önü kalkış"),
    ("44444444-4444-4444-4444-444444444444", "Orion AVM Önü", "Durak karşısı"),
)


def upgrade() -> None:
    for point_id, name, description in DEFAULT_BOARDING_POINTS:
        op.execute(
            "INSERT INTO boarding_points (id, name, description, is_active) "
            f"VALUES ('{point_id}'::uuid, '{name}', '{description}', TRUE) "
            "ON CONFLICT (id) DO NOTHING"
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM boarding_points "
        "WHERE id IN ('33333333-3333-3333-3333-333333333333'::uuid, "
        "'44444444-4444-4444-4444-444444444444'::uuid)"
    )
