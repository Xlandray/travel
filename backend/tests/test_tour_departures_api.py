"""Contract tests for the tour departure (bus stock) endpoints.

A departure row *is* the seat ledger: `available_seats` and `total_quota` are
what the booking code adds to and subtracts from. Anything that can write those
two numbers is therefore part of the money path, and these tests hold it to the
same invariant the booking tests do — `available_seats + held == total_quota`.
"""

import datetime
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from httpx import AsyncClient

from app.models.tour import Tour, TourDeparture

DepartureFactory = Callable[..., Awaitable[TourDeparture]]
SeatCheck = Callable[[TourDeparture], Awaitable[None]]

START = "2030-06-01"
END = "2030-06-05"


def payload(tour: Tour, **overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "tour_id": str(tour.id),
        "start_date": START,
        "end_date": END,
        "price": 1500.0,
        "total_quota": 45,
    }
    body.update(overrides)
    return body


class TestCreate:
    async def test_a_departure_starts_with_every_seat_on_sale(
        self, admin_client: AsyncClient, tour: Tour
    ) -> None:
        response = await admin_client.post("/tour-departures", json=payload(tour))
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["total_quota"] == 45
        assert body["available_seats"] == 45

    async def test_an_unknown_tour_is_a_404(self, admin_client: AsyncClient, tour: Tour) -> None:
        response = await admin_client.post(
            "/tour-departures", json=payload(tour, tour_id=str(uuid.uuid4()))
        )
        assert response.status_code == 404

    async def test_anonymous_callers_cannot_create_stock(
        self, client: AsyncClient, tour: Tour
    ) -> None:
        assert (await client.post("/tour-departures", json=payload(tour))).status_code == 401

    async def test_an_ordinary_user_cannot_create_stock(
        self, customer_client: AsyncClient, tour: Tour
    ) -> None:
        response = await customer_client.post("/tour-departures", json=payload(tour))
        assert response.status_code == 403

    async def test_seats_on_sale_cannot_exceed_the_bus(
        self, admin_client: AsyncClient, tour: Tour
    ) -> None:
        """Otherwise the ledger is broken before a single booking is made."""
        response = await admin_client.post(
            "/tour-departures", json=payload(tour, total_quota=45, available_seats=500)
        )
        assert response.status_code == 422

    async def test_a_departure_cannot_end_before_it_starts(
        self, admin_client: AsyncClient, tour: Tour
    ) -> None:
        response = await admin_client.post(
            "/tour-departures", json=payload(tour, start_date=END, end_date=START)
        )
        assert response.status_code == 422

    async def test_a_single_day_departure_is_allowed(
        self, admin_client: AsyncClient, tour: Tour
    ) -> None:
        response = await admin_client.post(
            "/tour-departures", json=payload(tour, start_date=START, end_date=START)
        )
        assert response.status_code == 201, response.text

    @pytest.mark.parametrize(
        "overrides",
        [
            {"total_quota": 0},
            {"total_quota": -1},
            {"price": -1},
            {"available_seats": -1},
        ],
    )
    async def test_out_of_range_values_are_rejected(
        self, admin_client: AsyncClient, tour: Tour, overrides: dict[str, Any]
    ) -> None:
        response = await admin_client.post("/tour-departures", json=payload(tour, **overrides))
        assert response.status_code == 422

    async def test_unknown_fields_are_rejected(self, admin_client: AsyncClient, tour: Tour) -> None:
        """Every other request schema forbids extras; this one must not differ."""
        response = await admin_client.post("/tour-departures", json=payload(tour, surprise="hello"))
        assert response.status_code == 422


class TestListAndRead:
    async def test_the_plain_list_is_an_array(
        self, admin_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        await make_departure()
        response = await admin_client.get("/tour-departures")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_paging_returns_the_refine_shape(
        self, admin_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        await make_departure()
        response = await admin_client.get("/tour-departures", params={"page": 1, "page_size": 10})
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)
        assert body["total"] >= 1

    async def test_the_list_can_be_filtered_by_tour(
        self, admin_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        mine = await make_departure()
        await make_departure()

        response = await admin_client.get("/tour-departures", params={"tour_id": str(mine.tour_id)})
        assert response.status_code == 200
        assert [d["id"] for d in response.json()] == [str(mine.id)]

    async def test_an_unknown_departure_is_a_404(self, admin_client: AsyncClient) -> None:
        assert (await admin_client.get(f"/tour-departures/{uuid.uuid4()}")).status_code == 404


class TestUpdate:
    async def test_the_price_can_be_changed(
        self, admin_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        response = await admin_client.patch(
            f"/tour-departures/{departure.id}", json={"price": 999.5}
        )
        assert response.status_code == 200
        assert response.json()["price"] == pytest.approx(999.5)

    async def test_an_ordinary_user_cannot_change_stock(
        self, customer_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        response = await customer_client.patch(
            f"/tour-departures/{departure.id}", json={"price": 1.0}
        )
        assert response.status_code == 403

    async def test_seats_on_sale_cannot_be_raised_above_the_bus(
        self, admin_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure(quota=45)
        response = await admin_client.patch(
            f"/tour-departures/{departure.id}", json={"available_seats": 500}
        )
        assert response.status_code == 422

    async def test_growing_the_bus_puts_the_new_seats_on_sale(
        self,
        admin_client: AsyncClient,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        """Held seats stay held; the difference goes on sale."""
        departure = await make_departure(quota=10)
        await customer_client.post(
            "/bookings/", json={"departure_id": str(departure.id), "seat_count": 4}
        )

        response = await admin_client.patch(
            f"/tour-departures/{departure.id}", json={"total_quota": 20}
        )

        assert response.status_code == 200, response.text
        assert response.json()["available_seats"] == 16
        await assert_seats_balance(departure)

    async def test_shrinking_the_bus_takes_seats_off_sale(
        self,
        admin_client: AsyncClient,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        departure = await make_departure(quota=10)
        await customer_client.post(
            "/bookings/", json={"departure_id": str(departure.id), "seat_count": 4}
        )

        response = await admin_client.patch(
            f"/tour-departures/{departure.id}", json={"total_quota": 6}
        )

        assert response.status_code == 200, response.text
        assert response.json()["available_seats"] == 2
        await assert_seats_balance(departure)

    async def test_the_bus_cannot_shrink_below_the_seats_already_sold(
        self,
        admin_client: AsyncClient,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
        assert_seats_balance: SeatCheck,
    ) -> None:
        """Four passengers are booked; a three-seat bus cannot carry them."""
        departure = await make_departure(quota=10)
        await customer_client.post(
            "/bookings/", json={"departure_id": str(departure.id), "seat_count": 4}
        )

        response = await admin_client.patch(
            f"/tour-departures/{departure.id}", json={"total_quota": 3}
        )

        assert response.status_code == 409
        await assert_seats_balance(departure)

    async def test_dates_cannot_be_inverted_by_an_update(
        self, admin_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        response = await admin_client.patch(
            f"/tour-departures/{departure.id}",
            json={"end_date": str(departure.start_date - datetime.timedelta(days=1))},
        )
        assert response.status_code == 422

    async def test_a_departure_cannot_be_moved_to_another_tour(
        self, admin_client: AsyncClient, make_departure: DepartureFactory, tour: Tour
    ) -> None:
        """Bookings point at this departure; their customers bought that trip.

        The backend used to drop `tour_id` on the floor, so the admin form's
        tour selector looked like it worked and never did.
        """
        departure = await make_departure()
        response = await admin_client.patch(
            f"/tour-departures/{departure.id}", json={"tour_id": str(tour.id)}
        )
        assert response.status_code == 422

    async def test_an_unknown_departure_is_a_404(self, admin_client: AsyncClient) -> None:
        response = await admin_client.patch(f"/tour-departures/{uuid.uuid4()}", json={"price": 1.0})
        assert response.status_code == 404


class TestDelete:
    async def test_an_unused_departure_can_be_deleted(
        self, admin_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        assert (await admin_client.delete(f"/tour-departures/{departure.id}")).status_code == 204
        assert (await admin_client.get(f"/tour-departures/{departure.id}")).status_code == 404

    async def test_a_departure_with_bookings_cannot_be_deleted(
        self,
        admin_client: AsyncClient,
        customer_client: AsyncClient,
        make_departure: DepartureFactory,
    ) -> None:
        """The booking rows reference it; deleting would orphan paid history."""
        departure = await make_departure()
        await customer_client.post(
            "/bookings/", json={"departure_id": str(departure.id), "seat_count": 1}
        )

        response = await admin_client.delete(f"/tour-departures/{departure.id}")
        assert response.status_code == 409

    async def test_an_ordinary_user_cannot_delete(
        self, customer_client: AsyncClient, make_departure: DepartureFactory
    ) -> None:
        departure = await make_departure()
        response = await customer_client.delete(f"/tour-departures/{departure.id}")
        assert response.status_code == 403

    async def test_an_unknown_departure_is_a_404(self, admin_client: AsyncClient) -> None:
        assert (await admin_client.delete(f"/tour-departures/{uuid.uuid4()}")).status_code == 404
