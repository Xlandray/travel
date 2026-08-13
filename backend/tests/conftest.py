"""Shared test fixtures.

Tests run against a real PostgreSQL instance, in a database separate from the
development one, whose schema is built by running the actual Alembic chain. That
way a migration that does not apply cleanly fails the suite.

Each test gets a session wrapped in a transaction that is rolled back afterwards,
so tests never see each other's rows even though the code under test commits.
"""

import os
import subprocess
import uuid
from collections.abc import AsyncIterator
from urllib.parse import urlsplit, urlunsplit

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.api.deps import get_current_superuser, get_current_user
from app.core.config import get_settings
from app.db.session import get_session
from app.main import app
from app.models import User

TEST_DB_SUFFIX = "_test"


def _swap_database(url: str, database: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(parts._replace(path=f"/{database}"))


@pytest.fixture(scope="session")
def dev_database_url() -> str:
    url = os.environ.get("DATABASE_URL") or get_settings().database_url
    return str(url)


@pytest.fixture(scope="session")
async def test_database_url(dev_database_url: str) -> AsyncIterator[str]:
    """Create a dedicated test database and migrate it to head.

    asyncpg is used directly for CREATE/DROP DATABASE, which cannot run inside a
    transaction block. Alembic's env.py calls asyncio.run(), so it cannot be
    invoked from inside a running event loop; it runs as a subprocess instead,
    which also exercises the same entry point the migrate container uses.
    """
    source_db = urlsplit(dev_database_url).path.lstrip("/")
    test_db = f"{source_db}{TEST_DB_SUFFIX}"
    test_url = _swap_database(dev_database_url, test_db)
    admin_dsn = _swap_database(dev_database_url, "postgres").replace("+asyncpg", "")

    connection = await asyncpg.connect(dsn=admin_dsn)
    try:
        await connection.execute(f'DROP DATABASE IF EXISTS "{test_db}" WITH (FORCE)')
        await connection.execute(f'CREATE DATABASE "{test_db}"')
    finally:
        await connection.close()

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env={**os.environ, "DATABASE_URL": test_url},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"alembic upgrade head failed on the test database:\n{result.stderr}")

    yield test_url


@pytest.fixture(scope="session")
async def engine(test_database_url: str) -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(test_database_url, poolclass=None)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """A session whose writes are rolled back when the test finishes.

    `join_transaction_mode="create_savepoint"` means commits inside the code
    under test land on a savepoint, so they are visible to the test but still
    disappear with the outer rollback.
    """
    async with engine.connect() as connection:
        transaction = await connection.begin()
        db = AsyncSession(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield db
        finally:
            await db.close()
            await transaction.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """An HTTP client bound to the app, sharing the test's rolled-back session."""

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def superuser(session: AsyncSession) -> User:
    user = User(
        email=f"admin-{uuid.uuid4().hex[:8]}@test.local",
        hashed_password="not-used-tests-override-auth",
        full_name="Test Admin",
        is_active=True,
        is_superuser=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def admin_client(client: AsyncClient, superuser: User) -> AsyncIterator[AsyncClient]:
    """A client authenticated as a superuser.

    The auth dependencies are overridden rather than a real token minted: these
    tests are about the hotel/slug contract, and going through the password flow
    would couple them to the hashing configuration.
    """
    app.dependency_overrides[get_current_user] = lambda: superuser
    app.dependency_overrides[get_current_superuser] = lambda: superuser
    yield client
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_superuser, None)
