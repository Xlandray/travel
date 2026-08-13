"""Races on the seat and money paths.

The rest of the suite shares one connection whose transaction is rolled back at
the end. That is the right trade for contract tests, but it cannot test row
locking at all: `SELECT ... FOR UPDATE` never blocks against your own
transaction, so a missing lock looks exactly like a working one.

These tests therefore run each request on its own session, from a real
sessionmaker, and commit for real. Auth is not overridden either — tokens are
minted with the application's own `create_access_token`, so concurrent requests
can come from different accounts. What is committed is deleted again by the
fixture, since there is no rollback to hide behind.
"""

import asyncio
import datetime
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.security import create_access_token
from app.db.session import get_session
from app.main import app
from app.models import User
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.tour import Tour, TourDeparture

SessionFactory = async_sessionmaker[AsyncSession]


@pytest.fixture
def live_sessions(engine: AsyncEngine) -> SessionFactory:
    """Independent sessions, each with its own connection and transaction."""
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def live_client(live_sessions: SessionFactory) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with live_sessions() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        yield client
    app.dependency_overrides.clear()


@dataclass
class World:
    departure_id: uuid.UUID
    tour_id: uuid.UUID
    user_ids: list[uuid.UUID]
    tokens: list[str]
    quota: int


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def world(live_sessions: SessionFactory) -> AsyncIterator[World]:
    """Committed rows, visible to every connection, removed afterwards."""
    quota = 5
    async with live_sessions() as session:
        tour = Tour(
            title="Yarış Turu",
            slug=f"yaris-turu-{uuid.uuid4().hex[:8]}",
            description="Concurrency fixture.",
            days=1,
            nights=0,
        )
        session.add(tour)
        await session.flush()

        departure = TourDeparture(
            tour_id=tour.id,
            start_date=datetime.date(2030, 9, 1),
            end_date=datetime.date(2030, 9, 2),
            price=Decimal("1000.00"),
            total_quota=quota,
            available_seats=quota,
        )
        session.add(departure)

        users = [
            User(
                email=f"race-{uuid.uuid4().hex[:10]}@test.local",
                hashed_password="not-used-token-auth",
                full_name=f"Yarışmacı {index}",
                is_active=True,
                is_superuser=index == 0,
            )
            for index in range(10)
        ]
        session.add_all(users)
        await session.commit()

        state = World(
            departure_id=departure.id,
            tour_id=tour.id,
            user_ids=[u.id for u in users],
            tokens=[create_access_token(str(u.id)) for u in users],
            quota=quota,
        )

    yield state

    async with live_sessions() as session:
        booking_ids = select(Booking.id).where(Booking.departure_id == state.departure_id)
        await session.execute(delete(Payment).where(Payment.booking_id.in_(booking_ids)))
        await session.execute(delete(Booking).where(Booking.departure_id == state.departure_id))
        await session.execute(delete(TourDeparture).where(TourDeparture.id == state.departure_id))
        await session.execute(delete(Tour).where(Tour.id == state.tour_id))
        await session.execute(delete(User).where(User.id.in_(state.user_ids)))
        await session.commit()


async def seats_left(sessions: SessionFactory, departure_id: uuid.UUID) -> int:
    async with sessions() as session:
        result = await session.execute(
            select(TourDeparture.available_seats).where(TourDeparture.id == departure_id)
        )
        return int(result.scalar_one())


async def held_seats(sessions: SessionFactory, departure_id: uuid.UUID) -> int:
    async with sessions() as session:
        result = await session.execute(
            select(Booking.seat_count).where(
                Booking.departure_id == departure_id, Booking.status != "cancelled"
            )
        )
        return sum(result.scalars().all())


class TestSeatRace:
    async def test_the_last_seats_cannot_be_sold_twice(
        self, live_client: AsyncClient, live_sessions: SessionFactory, world: World
    ) -> None:
        """Ten accounts go for five seats at once; five must lose.

        This is what `with_for_update` in `create_booking` is there for. Without
        the lock every request reads `available_seats` before any of them writes,
        and they all think there is room.
        """
        responses = await asyncio.gather(
            *(
                live_client.post(
                    "/bookings/",
                    json={"departure_id": str(world.departure_id), "seat_count": 1},
                    headers=auth(token),
                )
                for token in world.tokens
            )
        )

        codes = [r.status_code for r in responses]
        assert codes.count(201) == world.quota, codes
        assert codes.count(409) == len(world.tokens) - world.quota, codes

        left = await seats_left(live_sessions, world.departure_id)
        held = await held_seats(live_sessions, world.departure_id)
        assert left == 0
        assert left + held == world.quota

    async def test_a_multi_seat_race_does_not_oversell(
        self, live_client: AsyncClient, live_sessions: SessionFactory, world: World
    ) -> None:
        """Five accounts want two seats each out of five: at most two can win."""
        responses = await asyncio.gather(
            *(
                live_client.post(
                    "/bookings/",
                    json={"departure_id": str(world.departure_id), "seat_count": 2},
                    headers=auth(token),
                )
                for token in world.tokens[:5]
            )
        )

        codes = [r.status_code for r in responses]
        assert codes.count(201) == 2, codes

        left = await seats_left(live_sessions, world.departure_id)
        held = await held_seats(live_sessions, world.departure_id)
        assert left >= 0
        assert left + held == world.quota

    async def test_cancelling_concurrently_returns_each_seat_once(
        self, live_client: AsyncClient, live_sessions: SessionFactory, world: World
    ) -> None:
        """Duplicate cancels of one booking must not inflate the quota."""
        created = await live_client.post(
            "/bookings/",
            json={"departure_id": str(world.departure_id), "seat_count": 3},
            headers=auth(world.tokens[1]),
        )
        assert created.status_code == 201, created.text
        booking_id = created.json()["id"]

        await asyncio.gather(
            *(
                live_client.post(f"/bookings/{booking_id}/cancel", headers=auth(world.tokens[1]))
                for _ in range(4)
            )
        )

        left = await seats_left(live_sessions, world.departure_id)
        held = await held_seats(live_sessions, world.departure_id)
        assert left == world.quota
        assert left + held == world.quota


class TestPaymentRace:
    async def test_a_booking_cannot_be_charged_twice_at_once(
        self, live_client: AsyncClient, world: World
    ) -> None:
        """Two open attempts, paid simultaneously: only one may go through.

        Both are legitimately PENDING, so the guard that has to hold is the one
        on the booking. Without a lock both readers see a PENDING booking and
        both charge it.
        """
        token = world.tokens[1]
        created = await live_client.post(
            "/bookings/",
            json={"departure_id": str(world.departure_id), "seat_count": 1},
            headers=auth(token),
        )
        booking_id = created.json()["id"]

        attempts = []
        for method in ("card", "transfer"):
            opened = await live_client.post(
                "/payments/",
                json={"booking_id": booking_id, "method": method},
                headers=auth(token),
            )
            assert opened.status_code == 201, opened.text
            attempts.append(opened.json()["id"])

        responses = await asyncio.gather(
            *(
                live_client.post(f"/payments/{payment_id}/pay", headers=auth(token))
                for payment_id in attempts
            )
        )

        codes = [r.status_code for r in responses]
        assert codes.count(200) == 1, codes

    async def test_opening_payments_concurrently_cannot_double_charge(
        self, live_client: AsyncClient, world: World
    ) -> None:
        """Racing the open-then-pay flow must still settle a booking once."""
        token = world.tokens[2]
        created = await live_client.post(
            "/bookings/",
            json={"departure_id": str(world.departure_id), "seat_count": 1},
            headers=auth(token),
        )
        booking_id = created.json()["id"]

        async def open_and_pay(method: str) -> int:
            opened = await live_client.post(
                "/payments/",
                json={"booking_id": booking_id, "method": method},
                headers=auth(token),
            )
            if opened.status_code != 201:
                return opened.status_code
            paid = await live_client.post(
                f"/payments/{opened.json()['id']}/pay", headers=auth(token)
            )
            return paid.status_code

        codes = await asyncio.gather(*(open_and_pay(m) for m in ("card", "transfer", "card")))
        assert codes.count(200) == 1, codes

    async def test_a_payment_cannot_be_refunded_twice_at_once(
        self, live_client: AsyncClient, live_sessions: SessionFactory, world: World
    ) -> None:
        """Concurrent refunds must not pay the customer back twice."""
        customer, admin = world.tokens[3], world.tokens[0]
        created = await live_client.post(
            "/bookings/",
            json={"departure_id": str(world.departure_id), "seat_count": 2},
            headers=auth(customer),
        )
        booking_id = created.json()["id"]
        opened = await live_client.post(
            "/payments/",
            json={"booking_id": booking_id, "method": "card"},
            headers=auth(customer),
        )
        payment_id = opened.json()["id"]
        paid = await live_client.post(f"/payments/{payment_id}/pay", headers=auth(customer))
        assert paid.status_code == 200, paid.text

        responses = await asyncio.gather(
            *(
                live_client.post(f"/admin/payments/{payment_id}/refund", headers=auth(admin))
                for _ in range(3)
            )
        )

        codes = [r.status_code for r in responses]
        assert codes.count(200) == 1, codes

        left = await seats_left(live_sessions, world.departure_id)
        held = await held_seats(live_sessions, world.departure_id)
        assert left + held == world.quota


class TestMixedStorm:
    async def test_mixed_traffic_neither_deadlocks_nor_breaks_the_ledger(
        self, live_client: AsyncClient, live_sessions: SessionFactory, world: World
    ) -> None:
        """Book, cancel, pay and refund all at once on one departure.

        Every path takes its locks in the same order (booking, then payment,
        then departure). If any of them disagreed, PostgreSQL would break the
        cycle by aborting a transaction with a deadlock error, which surfaces
        here as a 500 — so "no 5xx" is the deadlock assertion. The ledger check
        is the correctness one.
        """
        admin = world.tokens[0]

        async def full_flow(token: str, refund: bool) -> list[int]:
            codes = []
            created = await live_client.post(
                "/bookings/",
                json={"departure_id": str(world.departure_id), "seat_count": 1},
                headers=auth(token),
            )
            codes.append(created.status_code)
            if created.status_code != 201:
                return codes

            booking_id = created.json()["id"]
            opened = await live_client.post(
                "/payments/",
                json={"booking_id": booking_id, "method": "card"},
                headers=auth(token),
            )
            codes.append(opened.status_code)
            if opened.status_code != 201:
                return codes

            payment_id = opened.json()["id"]
            paid = await live_client.post(f"/payments/{payment_id}/pay", headers=auth(token))
            codes.append(paid.status_code)

            if refund and paid.status_code == 200:
                refunded = await live_client.post(
                    f"/admin/payments/{payment_id}/refund", headers=auth(admin)
                )
                codes.append(refunded.status_code)
            elif not refund:
                cancelled = await live_client.post(
                    f"/bookings/{booking_id}/cancel", headers=auth(token)
                )
                codes.append(cancelled.status_code)
            return codes

        results = await asyncio.wait_for(
            asyncio.gather(
                *(
                    full_flow(token, refund=index % 2 == 0)
                    for index, token in enumerate(world.tokens[1:])
                )
            ),
            timeout=60,
        )

        codes = [code for flow in results for code in flow]
        assert not [c for c in codes if c >= 500], codes

        left = await seats_left(live_sessions, world.departure_id)
        held = await held_seats(live_sessions, world.departure_id)
        assert left + held == world.quota, f"available={left} held={held}"

    async def test_pay_and_refund_racing_on_one_payment_do_not_deadlock(
        self, live_client: AsyncClient, live_sessions: SessionFactory, world: World
    ) -> None:
        """The one pairing that can actually form a lock cycle.

        `mock_pay` and `refund_payment` touch the same booking and the same
        payment. If one took them in the order booking→payment and the other
        payment→booking, two concurrent requests could hold one lock each and
        wait for the other; PostgreSQL breaks that by aborting a transaction,
        which arrives here as a 500. Several pairs race at once because a
        deadlock needs the two to interleave, and one pair may simply not.
        """
        admin = world.tokens[0]
        payments: list[tuple[str, str]] = []
        for token in world.tokens[1:6]:
            created = await live_client.post(
                "/bookings/",
                json={"departure_id": str(world.departure_id), "seat_count": 1},
                headers=auth(token),
            )
            assert created.status_code == 201, created.text
            opened = await live_client.post(
                "/payments/",
                json={"booking_id": created.json()["id"], "method": "card"},
                headers=auth(token),
            )
            assert opened.status_code == 201, opened.text
            payments.append((opened.json()["id"], token))

        calls = []
        for payment_id, token in payments:
            calls.append(live_client.post(f"/payments/{payment_id}/pay", headers=auth(token)))
            calls.append(
                live_client.post(f"/admin/payments/{payment_id}/refund", headers=auth(admin))
            )

        responses = await asyncio.wait_for(asyncio.gather(*calls), timeout=60)

        codes = [r.status_code for r in responses]
        assert not [c for c in codes if c >= 500], codes

        left = await seats_left(live_sessions, world.departure_id)
        held = await held_seats(live_sessions, world.departure_id)
        assert left + held == world.quota, f"available={left} held={held}"


class TestRealTokenAuth:
    """The token path itself, which the overridden fixtures never exercise."""

    async def test_a_minted_token_is_accepted(self, live_client: AsyncClient, world: World) -> None:
        response = await live_client.get("/bookings/me", headers=auth(world.tokens[1]))
        assert response.status_code == 200

    async def test_a_garbage_token_is_rejected(self, live_client: AsyncClient) -> None:
        response = await live_client.get("/bookings/me", headers=auth("not-a-jwt"))
        assert response.status_code == 401

    async def test_a_token_for_a_deleted_user_is_rejected(self, live_client: AsyncClient) -> None:
        response = await live_client.get(
            "/bookings/me", headers=auth(create_access_token(str(uuid.uuid4())))
        )
        assert response.status_code == 401

    async def test_an_ordinary_token_cannot_reach_admin_routes(
        self, live_client: AsyncClient, world: World
    ) -> None:
        response = await live_client.get("/admin/bookings", headers=auth(world.tokens[1]))
        assert response.status_code == 403
