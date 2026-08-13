"""The migration chain, in both directions.

The rest of the suite proves migrations apply: `conftest.py` builds its database
by running them. Nothing proved they come back off. That matters on the day a
deploy has to be rolled back — a downgrade that half-works leaves a database in
a state no `upgrade` will fix, and the discovery happens under exactly the
pressure you would not choose for it.

These tests use their own scratch database and never touch the one the rest of
the suite shares.
"""

import os
import subprocess
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import asyncpg
import pytest

BACKEND_ROOT = Path(__file__).resolve().parent.parent

# The bookkeeping table Alembic owns. Its contents are the one thing that is
# meant to differ between a fresh chain and a downgraded-then-upgraded one.
ALEMBIC_TABLE = "alembic_version"


def _swap(url: str, database: str) -> str:
    return urlunsplit(urlsplit(url)._replace(path=f"/{database}"))


def alembic(url: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the real Alembic entry point, the same one the migrate container uses."""
    return subprocess.run(
        ["alembic", *args],
        cwd=BACKEND_ROOT,
        env={**os.environ, "DATABASE_URL": url},
        capture_output=True,
        text=True,
    )


def run(url: str, *args: str) -> None:
    result = alembic(url, *args)
    if result.returncode != 0:
        pytest.fail(f"`alembic {' '.join(args)}` failed:\n{result.stdout}\n{result.stderr}")


@pytest.fixture
async def scratch_database_url(dev_database_url: str) -> AsyncIterator[str]:
    """An empty database of its own, dropped when the test ends."""
    name = f"migration_check_{uuid.uuid4().hex[:12]}"
    admin_dsn = _swap(dev_database_url, "postgres").replace("+asyncpg", "")

    connection = await asyncpg.connect(dsn=admin_dsn)
    try:
        await connection.execute(f'CREATE DATABASE "{name}"')
    finally:
        await connection.close()

    try:
        yield _swap(dev_database_url, name)
    finally:
        connection = await asyncpg.connect(dsn=admin_dsn)
        try:
            await connection.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        finally:
            await connection.close()


async def snapshot(url: str) -> dict[str, list[tuple[Any, ...]]]:
    """Everything the migrations are responsible for creating.

    Tables and columns are the obvious part. Enum types, functions and triggers
    are the part that gets forgotten: `DROP TABLE` leaves the enum behind, and
    the failure only shows up on the *next* upgrade as "type already exists" —
    one step removed from the migration that caused it.
    """
    connection = await asyncpg.connect(dsn=url.replace("+asyncpg", ""))
    try:
        queries = {
            "columns": """
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name <> $1
                ORDER BY table_name, column_name
            """,
            "enums": """
                SELECT t.typname, e.enumlabel
                FROM pg_type t
                JOIN pg_enum e ON e.enumtypid = t.oid
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE n.nspname = 'public'
                ORDER BY t.typname, e.enumsortorder
            """,
            "indexes": """
                SELECT tablename, indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public' AND tablename <> $1
                ORDER BY tablename, indexname
            """,
            "constraints": """
                SELECT c.conrelid::regclass::text, c.conname, pg_get_constraintdef(c.oid)
                FROM pg_constraint c
                JOIN pg_namespace n ON n.oid = c.connamespace
                WHERE n.nspname = 'public' AND c.conrelid::regclass::text <> $1
                ORDER BY 1, 2
            """,
            # Extension-owned functions are excluded (`pg_depend.deptype = 'e'`).
            # The initial migration installs pgcrypto with `IF NOT EXISTS`,
            # which is an admission that it may already have been there — so
            # dropping it on the way down is not this chain's call to make, and
            # its several dozen functions are not leftovers.
            "functions": """
                SELECT p.proname, pg_get_functiondef(p.oid)
                FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname = 'public'
                  AND NOT EXISTS (
                      SELECT 1 FROM pg_depend d
                      WHERE d.objid = p.oid AND d.deptype = 'e'
                  )
                ORDER BY p.proname
            """,
            "triggers": """
                SELECT c.relname, t.tgname, pg_get_triggerdef(t.oid)
                FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND NOT t.tgisinternal
                ORDER BY c.relname, t.tgname
            """,
        }
        taken: dict[str, list[tuple[Any, ...]]] = {}
        for name, sql in queries.items():
            rows = await connection.fetch(sql, *([ALEMBIC_TABLE] if "$1" in sql else []))
            taken[name] = [tuple(row) for row in rows]
        return taken
    finally:
        await connection.close()


class TestTheChainIsReversible:
    async def test_downgrading_to_base_leaves_nothing_behind(
        self, scratch_database_url: str
    ) -> None:
        """A rollback has to actually undo the schema, not most of it.

        Enum types are the usual leftover: dropping the table does not drop the
        type, and the mess only surfaces on the next upgrade.
        """
        empty = await snapshot(scratch_database_url)
        assert empty == {key: [] for key in empty}, "the scratch database was not empty"

        run(scratch_database_url, "upgrade", "head")
        assert await snapshot(scratch_database_url) != empty

        run(scratch_database_url, "downgrade", "base")

        left_over = await snapshot(scratch_database_url)
        assert left_over == empty, f"downgrade left objects behind: {left_over}"

    async def test_the_schema_is_identical_after_a_round_trip(
        self, scratch_database_url: str
    ) -> None:
        """Down and back up must land on the same schema as going straight up.

        Catches the subtler half: a downgrade that drops something an earlier
        migration created, so the second upgrade builds a database that is
        quietly different from every other installation's.
        """
        run(scratch_database_url, "upgrade", "head")
        straight_up = await snapshot(scratch_database_url)

        run(scratch_database_url, "downgrade", "base")
        run(scratch_database_url, "upgrade", "head")
        round_trip = await snapshot(scratch_database_url)

        for section in straight_up:
            assert round_trip[section] == straight_up[section], (
                f"{section} differ after a round trip"
            )

    async def test_every_revision_can_be_stepped_down_one_at_a_time(
        self, scratch_database_url: str
    ) -> None:
        """`downgrade base` runs the whole chain; this checks each link.

        A revision whose downgrade only works because a later one already
        removed the object would pass the full run and fail the day somebody
        rolls back a single deploy — which is the normal case.
        """
        run(scratch_database_url, "upgrade", "head")

        listing = alembic(scratch_database_url, "history", "--indicate-current")
        assert listing.returncode == 0, listing.stderr
        steps = [line for line in listing.stdout.splitlines() if " -> " in line]
        assert len(steps) >= 8, f"expected the full chain, saw:\n{listing.stdout}"

        for _ in steps:
            run(scratch_database_url, "downgrade", "-1")

        left_over = await snapshot(scratch_database_url)
        assert left_over == {key: [] for key in left_over}, (
            f"stepping down one revision at a time left objects behind: {left_over}"
        )
