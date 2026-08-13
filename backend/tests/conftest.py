"""Shared test fixtures.

Tests run against a real PostgreSQL instance, in a database separate from the
development one, whose schema is built by running the actual Alembic chain. That
way a migration that does not apply cleanly fails the suite.

Each test gets a session wrapped in a transaction that is rolled back afterwards,
so tests never see each other's rows even though the code under test commits.
"""

import datetime
import os
import subprocess
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from decimal import Decimal
from urllib.parse import urlsplit, urlunsplit

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_session
from app.main import app
from app.models import User
from app.models.booking import Booking, BookingStatus
from app.models.tour import BoardingPoint, Tour, TourDeparture

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

    `expire_on_commit=False` mirrors `AsyncSessionLocal` in `app/db/session.py`.
    It has to: with the default (True) every commit expires the loaded objects,
    so the next attribute read emits IO. Under an async session that raises
    MissingGreenlet — a failure the same code never produces in production. The
    fixture must run the app under production's session semantics, or the suite
    reports bugs that do not exist and misses the ones that do.
    """
    async with engine.connect() as connection:
        transaction = await connection.begin()
        db = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
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


async def _make_user(session: AsyncSession, *, is_superuser: bool, label: str) -> User:
    user = User(
        email=f"{label}-{uuid.uuid4().hex[:8]}@test.local",
        hashed_password="not-used-tests-override-auth",
        full_name=f"Test {label.title()}",
        is_active=True,
        is_superuser=is_superuser,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def superuser(session: AsyncSession) -> User:
    return await _make_user(session, is_superuser=True, label="admin")


@pytest.fixture
async def customer(session: AsyncSession) -> User:
    """An ordinary, non-privileged account."""
    return await _make_user(session, is_superuser=False, label="customer")


@pytest.fixture
async def other_customer(session: AsyncSession) -> User:
    """A second ordinary account, for ownership checks."""
    return await _make_user(session, is_superuser=False, label="intruder")


@pytest.fixture
def as_user(client: AsyncClient) -> Callable[[User], AsyncClient]:
    """Point the shared client at a given account.

    Only `get_current_user` is overridden. `get_current_superuser` depends on it,
    so the real privilege check still runs and a non-superuser really does get a
    403 from the admin routes. Overriding both would paper over exactly the
    authorization the admin tests are there to prove.

    Minting a real token instead would couple every test to the password hashing
    configuration; the token flow itself is not covered here (see `AGENTS.md`).
    """

    def _login(user: User) -> AsyncClient:
        app.dependency_overrides[get_current_user] = lambda: user
        return client

    return _login


@pytest.fixture
def admin_client(as_user: Callable[[User], AsyncClient], superuser: User) -> AsyncClient:
    return as_user(superuser)


@pytest.fixture
def customer_client(as_user: Callable[[User], AsyncClient], customer: User) -> AsyncClient:
    return as_user(customer)


DepartureFactory = Callable[..., Awaitable[TourDeparture]]


@pytest.fixture
async def make_departure(session: AsyncSession) -> DepartureFactory:
    """Build a tour with one departure whose quota and price are known."""

    async def _make(
        *,
        quota: int = 10,
        available_seats: int | None = None,
        price: Decimal = Decimal("1250.75"),
    ) -> TourDeparture:
        tour = Tour(
            title="Test Turu",
            slug=f"test-turu-{uuid.uuid4().hex[:8]}",
            description="Fixture tour.",
            days=3,
            nights=2,
        )
        session.add(tour)
        await session.flush()

        departure = TourDeparture(
            tour_id=tour.id,
            start_date=datetime.date(2030, 6, 1),
            end_date=datetime.date(2030, 6, 3),
            price=price,
            total_quota=quota,
            available_seats=quota if available_seats is None else available_seats,
        )
        session.add(departure)
        await session.commit()
        return departure

    return _make


@pytest.fixture
async def boarding_point(session: AsyncSession) -> BoardingPoint:
    point = BoardingPoint(name="Orion AVM Önü", is_active=True)
    session.add(point)
    await session.commit()
    return point


@pytest.fixture
def assert_seats_balance(
    session: AsyncSession,
) -> Callable[[TourDeparture], Awaitable[None]]:
    """The one invariant the booking and payment code exists to preserve.

    Every seat is either on sale or held by a booking that is not cancelled:

        available_seats + seats held by live bookings == total_quota

    A breach means the bus was oversold or seats were lost, so this is asserted
    after every state transition rather than only checking the row under test.
    """

    async def _check(departure: TourDeparture) -> None:
        await session.refresh(departure)
        result = await session.execute(
            select(func.coalesce(func.sum(Booking.seat_count), 0)).where(
                Booking.departure_id == departure.id,
                Booking.status != BookingStatus.CANCELLED,
            )
        )
        held = int(result.scalar_one())
        assert departure.available_seats + held == departure.total_quota, (
            f"seat ledger broken: available={departure.available_seats} + held={held} "
            f"!= quota={departure.total_quota}"
        )

    return _check
