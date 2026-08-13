"""Contract tests for the payment endpoints.

Money and seats move together here: paying confirms a booking, refunding cancels
it and gives the seats back. Every test that changes payment state therefore also
asserts the seat ledger, because a refund that forgets the seats is just as much
a bug as one that forgets the money.
"""

import uuid
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient

from app.models import User
from app.models.tour import TourDeparture

DepartureFactory = Callable[..., Awaitable[TourDeparture]]
SeatCheck = Callable[[TourDeparture], Awaitable[None]]
Login = Callable[[User], AsyncClient]


async def book(client: AsyncClient, departure: TourDeparture, seats: int = 1) -> dict[str, Any]:
    response = await client.post(
        "/bookings/", json={"departure_id": str(departure.id), "seat_count": seats}
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def open_payment(
    client: AsyncClient, booking_id: str, method: str = "card"
) -> dict[str, Any]:
    response = await client.post("/payments/", json={"booking_id": booking_id, "method": method})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


class TestOpenPayment:
    async def test_the_amount_is_snapshotted_from_the_booking(
        self, customer_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure(price=Decimal("1250.75"))
        booking = await book(customer_client, departure, seats=2)

        payment = await open_payment(customer_client, booking["id"])

        assert payment["status"] == "pending"
        assert payment["amount"] == pytest.approx(booking["total_price"])
        assert payment["amount"] == pytest.approx(2501.50)
        assert payment["transaction_id"] is None
        assert payment["paid_at"] is None

    async def test_the_client_cannot_dictate_the_amount(
        self, customer_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure(price=Decimal("1250.75"))
        booking = await book(customer_client, departure)
        response = await customer_client.post(
            "/payments/",
            json={"booking_id": booking["id"], "method": "card", "amount": 1.0},
        )
        assert response.status_code == 422

    async def test_paying_for_someone_elses_booking_is_refused(
        self,
        as_user: Login,
        customer: User,
        other_customer: User,
        make_departure: DepartureFactory,
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(customer), departure)

        response = await as_user(other_customer).post(
            "/payments/", json={"booking_id": booking["id"], "method": "card"}
        )
        assert response.status_code == 403

    async def test_an_unknown_booking_is_a_404(self, customer_client: AsyncClient) -> None:
        response = await customer_client.post(
            "/payments/", json={"booking_id": str(uuid.uuid4()), "method": "card"}
        )
        assert response.status_code == 404

    async def test_a_cancelled_booking_cannot_be_paid_for(
        self, customer_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        booking = await book(customer_client, departure)
        await customer_client.post(f"/bookings/{booking['id']}/cancel")

        response = await customer_client.post(
            "/payments/", json={"booking_id": booking["id"], "method": "card"}
        )
        assert response.status_code == 409

    async def test_an_already_paid_booking_cannot_be_charged_again(
        self, customer_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        booking = await book(customer_client, departure)
        first = await open_payment(customer_client, booking["id"])
        await customer_client.post(f"/payments/{first['id']}/pay")

        response = await customer_client.post(
            "/payments/", json={"booking_id": booking["id"], "method": "card"}
        )
        assert response.status_code == 409

    async def test_anonymous_callers_are_refused(self, client: AsyncClient) -> None:
        response = await client.post(
            "/payments/", json={"booking_id": str(uuid.uuid4()), "method": "card"}
        )
        assert response.status_code == 401


class TestPay:
    async def test_paying_confirms_the_booking_and_keeps_the_seats_held(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(customer_client, departure, seats=2)
        payment = await open_payment(customer_client, booking["id"])

        response = await customer_client.post(f"/payments/{payment['id']}/pay")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "paid"
        assert body["transaction_id"] is not None
        assert body["paid_at"] is not None

        confirmed = await customer_client.get(f"/bookings/{booking['id']}")
        assert confirmed.json()["status"] == "confirmed"
        await assert_seats_balance(departure)
        assert departure.available_seats == 3

    async def test_paying_twice_is_refused(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(customer_client, departure, seats=2)
        payment = await open_payment(customer_client, booking["id"])
        await customer_client.post(f"/payments/{payment['id']}/pay")

        response = await customer_client.post(f"/payments/{payment['id']}/pay")

        assert response.status_code == 409
        await assert_seats_balance(departure)

    async def test_two_open_attempts_cannot_both_be_charged(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        """A booking may have several open attempts, but only one may succeed."""
        departure = await make_departure(quota=5)
        booking = await book(customer_client, departure, seats=2)
        first = await open_payment(customer_client, booking["id"], method="card")
        second = await open_payment(customer_client, booking["id"], method="transfer")

        assert (await customer_client.post(f"/payments/{first['id']}/pay")).status_code == 200
        response = await customer_client.post(f"/payments/{second['id']}/pay")

        assert response.status_code == 409
        await assert_seats_balance(departure)

    async def test_a_cancelled_booking_cannot_be_paid(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(customer_client, departure, seats=2)
        payment = await open_payment(customer_client, booking["id"])
        await customer_client.post(f"/bookings/{booking['id']}/cancel")

        response = await customer_client.post(f"/payments/{payment['id']}/pay")

        assert response.status_code == 409
        await assert_seats_balance(departure)
        assert departure.available_seats == 5

    async def test_paying_someone_elses_payment_is_refused(
        self,
        as_user: Login,
        customer: User,
        other_customer: User,
        make_departure: DepartureFactory,
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(customer), departure)
        payment = await open_payment(as_user(customer), booking["id"])

        response = await as_user(other_customer).post(f"/payments/{payment['id']}/pay")
        assert response.status_code == 403

    async def test_an_unknown_payment_is_a_404(self, customer_client: AsyncClient) -> None:
        response = await customer_client.post(f"/payments/{uuid.uuid4()}/pay")
        assert response.status_code == 404


class TestCancelAfterPaying:
    async def test_a_confirmed_booking_is_not_silently_left_alone(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        """Self-service cancel must not report success while doing nothing.

        A CONFIRMED booking has money against it, so releasing the seats here
        would strand a paid customer; the refund route is the only correct exit.
        Either way the caller has to be told, not handed a 200 and a booking that
        is still confirmed.
        """
        departure = await make_departure(quota=5)
        booking = await book(customer_client, departure, seats=2)
        payment = await open_payment(customer_client, booking["id"])
        await customer_client.post(f"/payments/{payment['id']}/pay")

        response = await customer_client.post(f"/bookings/{booking['id']}/cancel")

        assert response.status_code == 409
        await assert_seats_balance(departure)
        assert departure.available_seats == 3


class TestListing:
    async def test_my_payments_list_shows_only_mine(
        self,
        as_user: Login,
        customer: User,
        other_customer: User,
        make_departure: DepartureFactory,
    ) -> None:
        departure = await make_departure(quota=10)
        mine = await open_payment(
            as_user(customer), (await book(as_user(customer), departure))["id"]
        )
        await open_payment(
            as_user(other_customer), (await book(as_user(other_customer), departure))["id"]
        )

        response = await as_user(customer).get("/payments/me")
        assert response.status_code == 200
        assert [p["id"] for p in response.json()] == [mine["id"]]

    async def test_another_users_payment_is_a_404(
        self,
        as_user: Login,
        customer: User,
        other_customer: User,
        make_departure: DepartureFactory,
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(customer), departure)
        payment = await open_payment(as_user(customer), booking["id"])

        response = await as_user(other_customer).get(f"/payments/{payment['id']}")
        assert response.status_code == 404


class TestAdminPayments:
    async def test_an_ordinary_user_is_refused(self, customer_client: AsyncClient) -> None:
        response = await customer_client.get("/admin/payments")
        assert response.status_code == 403

    async def test_the_admin_list_returns_the_refine_shape(
        self, as_user: Login, customer: User, superuser: User, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(customer), departure)
        await open_payment(as_user(customer), booking["id"])

        response = await as_user(superuser).get(
            "/admin/payments", params={"page": 1, "page_size": 10}
        )
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)
        assert body["total"] >= 1

    async def test_refunding_cancels_the_booking_and_releases_the_seats(
        self,
        as_user: Login,
        customer: User,
        superuser: User,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(as_user(customer), departure, seats=3)
        payment = await open_payment(as_user(customer), booking["id"])
        await as_user(customer).post(f"/payments/{payment['id']}/pay")
        assert departure.available_seats == 2

        response = await as_user(superuser).post(f"/admin/payments/{payment['id']}/refund")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "refunded"
        assert body["refunded_at"] is not None
        await assert_seats_balance(departure)
        assert departure.available_seats == 5

        cancelled = await as_user(superuser).get(f"/admin/bookings/{booking['id']}")
        assert cancelled.json()["status"] == "cancelled"

    async def test_refunding_twice_is_refused(
        self,
        as_user: Login,
        customer: User,
        superuser: User,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(as_user(customer), departure, seats=3)
        payment = await open_payment(as_user(customer), booking["id"])
        await as_user(customer).post(f"/payments/{payment['id']}/pay")
        admin = as_user(superuser)
        await admin.post(f"/admin/payments/{payment['id']}/refund")

        response = await admin.post(f"/admin/payments/{payment['id']}/refund")

        assert response.status_code == 409
        await assert_seats_balance(departure)
        assert departure.available_seats == 5

    async def test_an_unpaid_payment_cannot_be_refunded(
        self, as_user: Login, customer: User, superuser: User, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(customer), departure)
        payment = await open_payment(as_user(customer), booking["id"])

        response = await as_user(superuser).post(f"/admin/payments/{payment['id']}/refund")
        assert response.status_code == 409

    async def test_confirming_a_transfer_confirms_the_booking(
        self,
        as_user: Login,
        customer: User,
        superuser: User,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(as_user(customer), departure, seats=2)
        payment = await open_payment(as_user(customer), booking["id"], method="transfer")

        response = await as_user(superuser).post(f"/admin/payments/{payment['id']}/confirm")

        assert response.status_code == 200
        assert response.json()["status"] == "paid"
        confirmed = await as_user(superuser).get(f"/admin/bookings/{booking['id']}")
        assert confirmed.json()["status"] == "confirmed"
        await assert_seats_balance(departure)
        assert departure.available_seats == 3

    async def test_confirming_a_transfer_twice_is_refused(
        self, as_user: Login, customer: User, superuser: User, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(customer), departure)
        payment = await open_payment(as_user(customer), booking["id"], method="transfer")
        admin = as_user(superuser)
        await admin.post(f"/admin/payments/{payment['id']}/confirm")

        response = await admin.post(f"/admin/payments/{payment['id']}/confirm")
        assert response.status_code == 409

    async def test_a_transfer_for_a_cancelled_booking_cannot_be_confirmed(
        self,
        as_user: Login,
        customer: User,
        superuser: User,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        """The seats went back on sale when the booking was cancelled.

        Confirming the transfer anyway flips the booking to CONFIRMED without
        taking the seats off the shelf again, so the departure ends up holding
        more confirmed passengers than it has seats.
        """
        departure = await make_departure(quota=5)
        booking = await book(as_user(customer), departure, seats=3)
        payment = await open_payment(as_user(customer), booking["id"], method="transfer")
        await as_user(customer).post(f"/bookings/{booking['id']}/cancel")
        assert departure.available_seats == 5

        response = await as_user(superuser).post(f"/admin/payments/{payment['id']}/confirm")

        assert response.status_code == 409
        await assert_seats_balance(departure)

    async def test_an_unknown_payment_is_a_404(self, as_user: Login, superuser: User) -> None:
        response = await as_user(superuser).post(f"/admin/payments/{uuid.uuid4()}/confirm")
        assert response.status_code == 404
