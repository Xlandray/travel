"""The audit trail: who moved money or seats, and whether the record survives.

Every other suite asks whether an operation did the right thing. These ask
whether it left evidence — and whether that evidence is still there once the
rows it describes are gone, which is exactly when somebody would go looking.
"""

import uuid
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any

from httpx import AsyncClient
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.audit_log import AuditAction, AuditLog
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.tour import TourDeparture
from app.services.cleanup_service import release_expired_bookings

DepartureFactory = Callable[..., Awaitable[TourDeparture]]
Login = Callable[[User], AsyncClient]


async def book(client: AsyncClient, departure: TourDeparture, seats: int = 1) -> dict[str, Any]:
    response = await client.post(
        "/bookings/", json={"departure_id": str(departure.id), "seat_count": seats}
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def pay(client: AsyncClient, booking_id: str) -> dict[str, Any]:
    opened = await client.post("/payments/", json={"booking_id": booking_id, "method": "card"})
    assert opened.status_code == 201, opened.text
    payment_id = opened.json()["id"]
    paid = await client.post(f"/payments/{payment_id}/pay")
    assert paid.status_code == 200, paid.text
    body: dict[str, Any] = paid.json()
    return body


async def entries(
    session: AsyncSession, *, booking_id: uuid.UUID | str | None = None
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.seq)
    if booking_id is not None:
        stmt = stmt.where(
            AuditLog.booking_id
            == (uuid.UUID(booking_id) if isinstance(booking_id, str) else booking_id)
        )
    return list((await session.execute(stmt)).scalars().all())


def actions(rows: list[AuditLog]) -> list[AuditAction]:
    return [row.action for row in rows]


class TestWhatGetsRecorded:
    async def test_booking_records_the_customer_the_seats_and_the_money(
        self,
        customer_client: AsyncClient,
        customer: User,
        make_departure: DepartureFactory,
        session: AsyncSession,
    ) -> None:
        departure = await make_departure(price=Decimal("1250.75"), quota=10)
        booking = await book(customer_client, departure, seats=2)

        rows = await entries(session, booking_id=booking["id"])
        assert actions(rows) == [AuditAction.BOOKING_CREATED]

        row = rows[0]
        assert row.actor_id == customer.id
        assert row.actor_email == customer.email
        assert row.actor_is_superuser is False
        assert row.amount == Decimal("2501.50")
        assert row.detail == {
            "departure_id": str(departure.id),
            "seat_count": 2,
            "seats_left": 8,
        }

    async def test_paying_records_both_the_charge_and_the_confirmation(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        session: AsyncSession,
    ) -> None:
        departure = await make_departure(price=Decimal("500.00"))
        booking = await book(customer_client, departure)
        payment = await pay(customer_client, booking["id"])

        rows = await entries(session, booking_id=booking["id"])
        assert actions(rows) == [
            AuditAction.BOOKING_CREATED,
            AuditAction.PAYMENT_OPENED,
            AuditAction.PAYMENT_PAID,
            AuditAction.BOOKING_CONFIRMED,
        ]

        charge = rows[2]
        assert charge.payment_id == uuid.UUID(payment["id"])
        assert charge.amount == Decimal("500.00")
        assert charge.detail is not None
        assert charge.detail["transaction_id"] == payment["transaction_id"]

    async def test_a_refund_names_the_administrator_who_authorised_it(
        self,
        customer_client: AsyncClient,
        admin_client: AsyncClient,
        superuser: User,
        make_departure: DepartureFactory,
        session: AsyncSession,
    ) -> None:
        """Money leaving the business is the entry that matters most."""
        departure = await make_departure(price=Decimal("750.00"))
        booking = await book(customer_client, departure)
        payment = await pay(customer_client, booking["id"])

        refund = await admin_client.post(f"/admin/payments/{payment['id']}/refund")
        assert refund.status_code == 200, refund.text

        rows = await entries(session, booking_id=booking["id"])
        assert AuditAction.PAYMENT_REFUNDED in actions(rows)

        refunded = next(r for r in rows if r.action == AuditAction.PAYMENT_REFUNDED)
        assert refunded.actor_id == superuser.id
        assert refunded.actor_email == superuser.email
        assert refunded.actor_is_superuser is True
        assert refunded.amount == Decimal("750.00")

        # The cancellation that comes with it is its own fact, and it must not
        # read as the customer's decision.
        cancelled = next(r for r in rows if r.action == AuditAction.BOOKING_CANCELLED)
        assert cancelled.actor_id == superuser.id
        assert cancelled.detail == {"seat_count": 1, "by": "admin"}

    async def test_a_customer_cancelling_is_told_apart_from_an_admin_cancelling(
        self,
        customer_client: AsyncClient,
        customer: User,
        make_departure: DepartureFactory,
        session: AsyncSession,
    ) -> None:
        departure = await make_departure()
        booking = await book(customer_client, departure)

        cancelled = await customer_client.post(f"/bookings/{booking['id']}/cancel")
        assert cancelled.status_code == 200, cancelled.text

        rows = await entries(session, booking_id=booking["id"])
        entry = next(r for r in rows if r.action == AuditAction.BOOKING_CANCELLED)
        assert entry.actor_id == customer.id
        assert entry.detail is not None
        assert entry.detail["by"] == "customer"

    async def test_the_sweeper_records_no_actor(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        session: AsyncSession,
    ) -> None:
        """Nobody decided this; a timer did. The trail has to say so.

        An expiry attributed to the customer would read as them changing their
        mind, which is a different thing from an abandoned cart.
        """
        departure = await make_departure()
        booking = await book(customer_client, departure)

        stale = await session.get(Booking, uuid.UUID(booking["id"]))
        assert stale is not None
        await session.execute(
            update(Booking)
            .where(Booking.id == stale.id)
            .values(created_at=stale.created_at.replace(year=stale.created_at.year - 1))
        )
        await session.commit()

        assert await release_expired_bookings(session) >= 1

        rows = await entries(session, booking_id=booking["id"])
        expired = next(r for r in rows if r.action == AuditAction.BOOKING_EXPIRED)
        assert expired.actor_id is None
        assert expired.actor_email is None
        assert expired.detail is not None
        assert expired.detail["by"] == "sweeper"


class TestTheTrailOutlivesWhatItDescribes:
    async def test_deleting_the_booking_does_not_delete_its_history(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        session: AsyncSession,
    ) -> None:
        """The whole reason the table has no foreign keys.

        Payments are deleted with their booking (`ON DELETE CASCADE`). If the
        trail were wired up the same way, the record of a charge would vanish
        with the row it describes — and a log that disappears alongside the
        evidence is not a log.
        """
        departure = await make_departure(price=Decimal("300.00"))
        booking = await book(customer_client, departure)
        payment = await pay(customer_client, booking["id"])
        booking_uuid = uuid.UUID(booking["id"])

        before = await entries(session, booking_id=booking_uuid)
        assert len(before) == 4

        await session.execute(delete(Booking).where(Booking.id == booking_uuid))
        await session.commit()

        assert await session.get(Booking, booking_uuid) is None
        assert await session.get(Payment, uuid.UUID(payment["id"])) is None

        after = await entries(session, booking_id=booking_uuid)
        assert actions(after) == actions(before)
        assert after[2].amount == Decimal("300.00")

    async def test_the_entry_still_says_who_after_the_account_is_gone(
        self,
        as_user: Login,
        other_customer: User,
        make_departure: DepartureFactory,
        session: AsyncSession,
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(other_customer), departure)
        email = other_customer.email

        await session.execute(delete(User).where(User.id == other_customer.id))
        await session.commit()

        rows = await entries(session, booking_id=booking["id"])
        assert rows[0].actor_email == email


class TestNothingIsRecordedForWhatDidNotHappen:
    async def test_a_refused_booking_leaves_no_line(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        session: AsyncSession,
    ) -> None:
        """A log that records attempts as if they were events is worse than none."""
        departure = await make_departure(quota=2, available_seats=1)

        response = await customer_client.post(
            "/bookings/", json={"departure_id": str(departure.id), "seat_count": 2}
        )
        assert response.status_code == 409

        assert await entries(session) == []

    async def test_a_refused_refund_leaves_no_line(
        self,
        customer_client: AsyncClient,
        admin_client: AsyncClient,
        make_departure: DepartureFactory,
        session: AsyncSession,
    ) -> None:
        departure = await make_departure()
        booking = await book(customer_client, departure)
        opened = await customer_client.post(
            "/payments/", json={"booking_id": booking["id"], "method": "card"}
        )
        payment_id = opened.json()["id"]

        # Never paid, so there is nothing to give back.
        refund = await admin_client.post(f"/admin/payments/{payment_id}/refund")
        assert refund.status_code == 409

        rows = await entries(session, booking_id=booking["id"])
        assert AuditAction.PAYMENT_REFUNDED not in actions(rows)


class TestReadingTheTrail:
    async def test_an_ordinary_customer_cannot_read_it(self, customer_client: AsyncClient) -> None:
        assert (await customer_client.get("/admin/audit-logs")).status_code == 403

    async def test_it_is_read_only(self, admin_client: AsyncClient) -> None:
        """There is deliberately no way to edit or remove a line.

        A trail an administrator can tidy up proves nothing about the
        administrator.
        """
        listed = await admin_client.get("/admin/audit-logs")
        assert listed.status_code == 200

        for method, path in [
            ("delete", "/admin/audit-logs/{id}"),
            ("patch", "/admin/audit-logs/{id}"),
            ("post", "/admin/audit-logs"),
        ]:
            response = await getattr(admin_client, method)(
                path.format(id=uuid.uuid4()), **({"json": {}} if method != "delete" else {})
            )
            assert response.status_code in (404, 405), f"{method} {path} -> {response.status_code}"

    async def test_newest_first_and_filterable_by_booking(
        self,
        customer_client: AsyncClient,
        admin_client: AsyncClient,
        make_departure: DepartureFactory,
    ) -> None:
        departure = await make_departure()
        mine = await book(customer_client, departure)
        other = await book(customer_client, departure)
        await pay(customer_client, mine["id"])

        response = await admin_client.get("/admin/audit-logs", params={"booking_id": mine["id"]})
        assert response.status_code == 200, response.text
        body = response.json()

        assert body["total"] == 4
        assert [row["action"] for row in body["data"]] == [
            "booking.confirmed",
            "payment.paid",
            "payment.opened",
            "booking.created",
        ]
        assert all(row["booking_id"] == mine["id"] for row in body["data"])
        assert all(row["booking_id"] != other["id"] for row in body["data"])

    async def test_filtering_by_action_finds_the_money_that_left(
        self,
        customer_client: AsyncClient,
        admin_client: AsyncClient,
        make_departure: DepartureFactory,
    ) -> None:
        departure = await make_departure(price=Decimal("640.00"))
        booking = await book(customer_client, departure)
        payment = await pay(customer_client, booking["id"])
        await admin_client.post(f"/admin/payments/{payment['id']}/refund")

        response = await admin_client.get(
            "/admin/audit-logs", params={"action": "payment.refunded"}
        )
        assert response.status_code == 200, response.text
        body = response.json()

        assert body["total"] == 1
        assert Decimal(body["data"][0]["amount"]) == Decimal("640.00")
        assert body["data"][0]["payment_id"] == payment["id"]

    async def test_the_total_counts_matches_not_the_page(
        self,
        customer_client: AsyncClient,
        admin_client: AsyncClient,
        make_departure: DepartureFactory,
    ) -> None:
        """A count taken off the paged query would report the page size.

        Then the admin panel shows "1 of 1" while three entries exist, and
        pagination stops at the first page.
        """
        departure = await make_departure(quota=10)
        for _ in range(3):
            await book(customer_client, departure)

        response = await admin_client.get("/admin/audit-logs", params={"page_size": 1})
        assert response.status_code == 200
        body = response.json()

        assert len(body["data"]) == 1
        assert body["total"] == 3
