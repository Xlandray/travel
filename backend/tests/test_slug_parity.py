"""The application and the migration must produce the same slug.

This is a regression test. `generate_slug` used to only collapse whitespace
while migration c7a9b3f5d1e2 stripped every non-alphanumeric run, so the same
hotel name produced `cave-hotel-&-spa` through the API and `cave-hotel-spa`
through the backfill — one record, two URLs.

Rather than hard-coding the SQL, the expression is read out of the migration
file and executed. If someone edits the migration without editing
`app.core.slug`, this fails.
"""

import pathlib
import re

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.slug import generate_slug

MIGRATION = (
    pathlib.Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "c7a9b3f5d1e2_add_hotel_slug.py"
)

NAMES = [
    "Cave Hotel & Spa",
    "Ürgüp Konak Otel",
    "İstanbul Şehir Oteli",
    "ÇĞİÖŞÜ çğıöşü",
    "Hotel #1 (Deluxe)",
    "  Çift   Boşluk  ",
    "---abc---",
    "Otel 2026/08",
    "a-b_c.d",
    "Ada'nın Evi",
    "Ölüdeniz Beach Resort",
    "MAJUSKUL OTEL",
    "Dağ & Deniz — Butik",
    "Otel\tSekmeli",
    "!!! ###",
    "Bodrum",
]


def _slug_expression_from_migration() -> str:
    """Pull the `SET slug = <expr>` expression out of the migration, as SQL."""
    source = MIGRATION.read_text(encoding="utf-8")
    match = re.search(r"SET\s+slug\s*=\s*(.+?)\s*WHERE\b", source, re.S | re.I)
    if not match:
        pytest.fail(f"could not find the slug expression in {MIGRATION.name}")
    # The expression reads the `name` column; bind a value in its place instead.
    return re.sub(r"\bname\b", ":value", match.group(1))


def test_migration_still_exposes_a_slug_expression():
    expression = _slug_expression_from_migration()
    assert "translate(" in expression
    assert "regexp_replace(" in expression


@pytest.mark.parametrize("name", NAMES)
async def test_generate_slug_matches_the_migration(session: AsyncSession, name: str):
    expression = _slug_expression_from_migration()
    result = await session.execute(text(f"SELECT {expression}"), {"value": name})
    assert generate_slug(name) == result.scalar_one()


async def test_unslugable_name_yields_empty_on_both_sides(session: AsyncSession):
    """A name with nothing slug-able must be empty in Python too, not a stray '-'."""
    expression = _slug_expression_from_migration()
    result = await session.execute(text(f"SELECT {expression}"), {"value": "!!! ###"})
    assert result.scalar_one() == ""
    assert generate_slug("!!! ###") == ""
