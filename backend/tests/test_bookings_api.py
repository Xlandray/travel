"""Contract tests for the booking endpoints.

These are the seat-and-money paths, so nearly every test also asserts the seat
ledger invariant (see the `assert_seats_balance` fixture) rather than only the
status code: a route that returns the right code while leaking or duplicating
seats is still broken.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.booking import Booking
from app.models.tour import TourDeparture
from app.services.cleanup_service import release_expired_bookings

DepartureFactory = Callable[..., Awaitable[TourDeparture]]
SeatCheck = Callable[[TourDeparture], Awaitable[None]]
Login = Callable[[User], AsyncClient]


async def book(
    client: AsyncClient, departure: TourDeparture, seats: int = 1, **extra: object
) -> dict[str, Any]:
    response = await client.post(
        "/bookings/",
        json={"departure_id": str(departure.id), "seat_count": seats, **extra},
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


class TestCreate:
    async def test_a_booking_holds_seats_and_freezes_the_price(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=10, price=Decimal("1250.75"))

        booking = await book(customer_client, departure, seats=2)

        assert booking["status"] == "pending"
        assert booking["seat_count"] == 2
        # The price comes from the departure row, never from the request.
        assert booking["total_price"] == pytest.approx(2501.50)
        await assert_seats_balance(departure)
        assert departure.available_seats == 8

    async def test_the_client_cannot_dictate_the_price(
        self, customer_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        """`Schema` forbids extra fields, so a smuggled total_price is a 422."""
        departure = await make_departure(price=Decimal("1250.75"))
        response = await customer_client.post(
            "/bookings/",
            json={"departure_id": str(departure.id), "seat_count": 1, "total_price": 1.0},
        )
        assert response.status_code == 422

    async def test_the_last_seats_can_be_sold(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=3)
        await book(customer_client, departure, seats=3)
        await assert_seats_balance(departure)
        assert departure.available_seats == 0

    async def test_overselling_is_refused_and_changes_nothing(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=2)
        response = await customer_client.post(
            "/bookings/", json={"departure_id": str(departure.id), "seat_count": 3}
        )
        assert response.status_code == 409
        await assert_seats_balance(departure)
        assert departure.available_seats == 2

    async def test_a_sold_out_departure_refuses_further_bookings(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=1)
        await book(customer_client, departure, seats=1)
        response = await customer_client.post(
            "/bookings/", json={"departure_id": str(departure.id), "seat_count": 1}
        )
        assert response.status_code == 409
        await assert_seats_balance(departure)

    @pytest.mark.parametrize("seats", [0, -1, -5, 11])
    async def test_out_of_range_seat_counts_are_rejected(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
        seats: int,
    ) -> None:
        """A non-positive count would *add* seats to the departure if it landed."""
        departure = await make_departure(quota=10)
        response = await customer_client.post(
            "/bookings/", json={"departure_id": str(departure.id), "seat_count": seats}
        )
        assert response.status_code == 422
        await assert_seats_balance(departure)
        assert departure.available_seats == 10

    async def test_an_unknown_departure_is_a_404(self, customer_client: AsyncClient) -> None:
        response = await customer_client.post(
            "/bookings/", json={"departure_id": str(uuid.uuid4()), "seat_count": 1}
        )
        assert response.status_code == 404

    async def test_anonymous_callers_cannot_book(
        self, client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        response = await client.post(
            "/bookings/", json={"departure_id": str(departure.id), "seat_count": 1}
        )
        assert response.status_code == 401

    async def test_a_boarding_point_is_recorded(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        boarding_point: Any,
    ) -> None:
        departure = await make_departure()
        booking = await book(
            customer_client, departure, seats=1, boarding_point_id=str(boarding_point.id)
        )
        assert booking["boarding_point_id"] == str(boarding_point.id)


class TestOwnership:
    async def test_my_list_shows_only_my_bookings(
        self,
        as_user: Login,
        customer: User,
        other_customer: User,
        make_departure: DepartureFactory,
    ) -> None:
        departure = await make_departure(quota=10)
        mine = await book(as_user(customer), departure, seats=1)
        await book(as_user(other_customer), departure, seats=1)

        response = await as_user(customer).get("/bookings/me")
        assert response.status_code == 200
        ids = [b["id"] for b in response.json()]
        assert ids == [mine["id"]]

    async def test_another_users_booking_is_a_404(
        self,
        as_user: Login,
        customer: User,
        other_customer: User,
        make_departure: DepartureFactory,
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(customer), departure, seats=1)

        response = await as_user(other_customer).get(f"/bookings/{booking['id']}")
        assert response.status_code == 404

    async def test_a_superuser_can_read_any_booking(
        self,
        as_user: Login,
        customer: User,
        superuser: User,
        make_departure: DepartureFactory,
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(customer), departure, seats=1)

        response = await as_user(superuser).get(f"/bookings/{booking['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == booking["id"]

    async def test_another_user_cannot_cancel_my_booking(
        self,
        as_user: Login,
        customer: User,
        other_customer: User,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(as_user(customer), departure, seats=2)

        response = await as_user(other_customer).post(f"/bookings/{booking['id']}/cancel")
        assert response.status_code == 404
        await assert_seats_balance(departure)
        assert departure.available_seats == 3


class TestCancel:
    async def test_cancelling_returns_the_seats(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(customer_client, departure, seats=2)
        assert departure.available_seats == 3

        response = await customer_client.post(f"/bookings/{booking['id']}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
        await assert_seats_balance(departure)
        assert departure.available_seats == 5

    async def test_cancelling_twice_does_not_return_the_seats_twice(
        self,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        """The second call must be a no-op; otherwise the quota inflates."""
        departure = await make_departure(quota=5)
        booking = await book(customer_client, departure, seats=2)

        await customer_client.post(f"/bookings/{booking['id']}/cancel")
        await customer_client.post(f"/bookings/{booking['id']}/cancel")

        await assert_seats_balance(departure)
        assert departure.available_seats == 5

    async def test_an_unknown_booking_is_a_404(self, customer_client: AsyncClient) -> None:
        response = await customer_client.post(f"/bookings/{uuid.uuid4()}/cancel")
        assert response.status_code == 404


class TestAdminRoutes:
    async def test_an_ordinary_user_is_refused(self, customer_client: AsyncClient) -> None:
        response = await customer_client.get("/admin/bookings")
        assert response.status_code == 403

    async def test_the_admin_list_returns_the_refine_shape(
        self, as_user: Login, customer: User, superuser: User, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        await book(as_user(customer), departure, seats=1)

        response = await as_user(superuser).get(
            "/admin/bookings", params={"page": 1, "page_size": 10}
        )
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)
        assert body["total"] >= 1

    async def test_the_admin_list_filters_by_status(
        self, as_user: Login, customer: User, superuser: User, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure(quota=10)
        keep = await book(as_user(customer), departure, seats=1)
        drop = await book(as_user(customer), departure, seats=1)
        await as_user(customer).post(f"/bookings/{drop['id']}/cancel")

        response = await as_user(superuser).get("/admin/bookings", params={"status": "pending"})
        assert response.status_code == 200
        ids = [b["id"] for b in response.json()["data"]]
        assert keep["id"] in ids
        assert drop["id"] not in ids

    async def test_admin_cancel_releases_the_seats(
        self,
        as_user: Login,
        customer: User,
        superuser: User,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(as_user(customer), departure, seats=3)

        response = await as_user(superuser).post(f"/admin/bookings/{booking['id']}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
        await assert_seats_balance(departure)
        assert departure.available_seats == 5

    async def test_admin_cancel_is_idempotent(
        self,
        as_user: Login,
        customer: User,
        superuser: User,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(as_user(customer), departure, seats=3)

        admin = as_user(superuser)
        await admin.post(f"/admin/bookings/{booking['id']}/cancel")
        await admin.post(f"/admin/bookings/{booking['id']}/cancel")

        await assert_seats_balance(departure)
        assert departure.available_seats == 5

    async def test_the_patch_route_only_accepts_confirmed(
        self, as_user: Login, customer: User, superuser: User, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        booking = await book(as_user(customer), departure, seats=1)

        response = await as_user(superuser).patch(
            f"/admin/bookings/{booking['id']}", json={"status": "cancelled"}
        )
        assert response.status_code == 422

    async def test_confirming_a_pending_booking_keeps_the_seats_held(
        self,
        as_user: Login,
        customer: User,
        superuser: User,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=5)
        booking = await book(as_user(customer), departure, seats=2)

        response = await as_user(superuser).patch(
            f"/admin/bookings/{booking['id']}", json={"status": "confirmed"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"
        await assert_seats_balance(departure)
        assert departure.available_seats == 3

    async def test_a_cancelled_booking_cannot_be_confirmed_back(
        self,
        as_user: Login,
        customer: User,
        superuser: User,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        """Its seats were already released; confirming would oversell the bus."""
        departure = await make_departure(quota=5)
        booking = await book(as_user(customer), departure, seats=3)
        admin = as_user(superuser)
        await admin.post(f"/admin/bookings/{booking['id']}/cancel")

        response = await admin.patch(
            f"/admin/bookings/{booking['id']}", json={"status": "confirmed"}
        )

        assert response.status_code == 409
        await assert_seats_balance(departure)
        assert departure.available_seats == 5


class TestSweeper:
    async def test_the_sweeper_releases_only_bookings_past_the_timeout(
        self,
        customer_client: AsyncClient,
        session: AsyncSession,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        """`release_expired_bookings` is what actually reclaims abandoned carts."""
        departure = await make_departure(quota=10)
        stale = await book(customer_client, departure, seats=2)
        fresh = await book(customer_client, departure, seats=1)

        await session.execute(
            update(Booking)
            .where(Booking.id == uuid.UUID(stale["id"]))
            .values(created_at=datetime.now(UTC) - timedelta(minutes=16))
        )
        await session.commit()

        released = await release_expired_bookings(session)

        assert released == 1
        await assert_seats_balance(departure)
        assert departure.available_seats == 9

        still_pending = await customer_client.get(f"/bookings/{fresh['id']}")
        assert still_pending.json()["status"] == "pending"
