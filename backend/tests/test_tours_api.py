"""Contract tests for the tour catalogue endpoints."""

import uuid
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tour import Tour


async def create(admin_client: AsyncClient, **payload: Any) -> dict[str, Any]:
    payload.setdefault("title", f"Kapadokya Turu {uuid.uuid4().hex[:6]}")
    payload.setdefault("description", "Üç gün iki gece.")
    response = await admin_client.post("/tours", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


class TestCreate:
    async def test_the_slug_is_derived_from_the_title(self, admin_client: AsyncClient) -> None:
        tour = await create(admin_client, title="Şirince Bağ Turu")
        assert tour["slug"] == "sirince-bag-turu"

    async def test_an_explicit_slug_is_kept(self, admin_client: AsyncClient) -> None:
        tour = await create(admin_client, title="Kapadokya", slug="cappadocia-tour")
        assert tour["slug"] == "cappadocia-tour"

    async def test_a_title_with_no_slugable_characters_is_rejected(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.post("/tours", json={"title": "!!! ###"})
        assert response.status_code == 422

    async def test_an_unknown_category_is_a_404(self, admin_client: AsyncClient) -> None:
        response = await admin_client.post(
            "/tours", json={"title": "Kategorisiz", "category_id": str(uuid.uuid4())}
        )
        assert response.status_code == 404

    async def test_an_ordinary_user_cannot_create(self, customer_client: AsyncClient) -> None:
        assert (await customer_client.post("/tours", json={"title": "Gizli"})).status_code == 403

    async def test_anonymous_callers_cannot_create(self, client: AsyncClient) -> None:
        assert (await client.post("/tours", json={"title": "Gizli"})).status_code == 401


class TestRead:
    async def test_a_tour_is_reachable_by_slug_and_by_uuid(self, admin_client: AsyncClient) -> None:
        created = await create(admin_client)

        by_slug = await admin_client.get(f"/tours/{created['slug']}")
        by_uuid = await admin_client.get(f"/tours/{created['id']}")

        assert by_slug.status_code == 200
        assert by_uuid.status_code == 200
        assert by_slug.json()["id"] == by_uuid.json()["id"] == created["id"]

    async def test_an_unknown_slug_is_a_404(self, client: AsyncClient) -> None:
        assert (await client.get("/tours/boyle-bir-tur-yok")).status_code == 404


class TestVisibility:
    async def test_the_public_list_hides_unpublished_tours(
        self, admin_client: AsyncClient, client: AsyncClient
    ) -> None:
        hidden = await create(admin_client, title="Taslak Tur", is_active=False)
        published = await create(admin_client, title="Yayindaki Tur")

        response = await client.get("/tours", params={"page": 1, "page_size": 50})
        assert response.status_code == 200
        ids = [t["id"] for t in response.json()["data"]]
        assert published["id"] in ids
        assert hidden["id"] not in ids

    async def test_an_admin_can_still_see_an_unpublished_tour(
        self, admin_client: AsyncClient
    ) -> None:
        """Otherwise unpublishing hides it from the only screen that can undo it."""
        hidden = await create(admin_client, title="Taslak Tur", is_active=False)

        response = await admin_client.get(
            "/tours", params={"page": 1, "page_size": 50, "include_inactive": True}
        )

        assert response.status_code == 200
        assert hidden["id"] in [t["id"] for t in response.json()["data"]]

    async def test_an_ordinary_user_cannot_ask_for_the_hidden_ones(
        self, customer_client: AsyncClient
    ) -> None:
        response = await customer_client.get("/tours", params={"include_inactive": True})
        assert response.status_code == 403

    async def test_anonymous_callers_cannot_ask_for_the_hidden_ones(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/tours", params={"include_inactive": True})
        assert response.status_code in (401, 403)

    async def test_an_empty_catalogue_serves_placeholder_tours(self, client: AsyncClient) -> None:
        """Pins existing behaviour rather than endorsing it.

        With no active tours the unpaginated list returns `DEFAULT_TOURS`, a
        hard-coded demo catalogue, so a fresh or fully unpublished database shows
        customers trips that do not exist. Pinned here so it cannot change or be
        removed by accident — see the note in AGENTS.md.
        """
        response = await client.get("/tours")
        assert response.status_code == 200
        body = response.json()
        assert body, "empty catalogue returned nothing; the placeholder behaviour changed"
        assert all(t["id"] for t in body)


class TestUpdateAndDelete:
    async def test_the_title_can_be_changed(self, admin_client: AsyncClient) -> None:
        tour = await create(admin_client)
        response = await admin_client.patch(f"/tours/{tour['id']}", json={"title": "Yeni Başlık"})
        assert response.status_code == 200
        assert response.json()["title"] == "Yeni Başlık"

    async def test_a_tour_can_be_unpublished_and_republished(
        self, admin_client: AsyncClient
    ) -> None:
        tour = await create(admin_client)
        off = await admin_client.patch(f"/tours/{tour['id']}", json={"is_active": False})
        assert off.status_code == 200
        assert off.json()["is_active"] is False

        on = await admin_client.patch(f"/tours/{tour['id']}", json={"is_active": True})
        assert on.status_code == 200
        assert on.json()["is_active"] is True

    async def test_taking_another_tours_slug_is_a_conflict(self, admin_client: AsyncClient) -> None:
        first = await create(admin_client)
        second = await create(admin_client)
        response = await admin_client.patch(f"/tours/{second['id']}", json={"slug": first["slug"]})
        assert response.status_code == 409

    async def test_an_ordinary_user_cannot_update(
        self, admin_client: AsyncClient, customer_client: AsyncClient
    ) -> None:
        tour = await create(admin_client)
        response = await customer_client.patch(f"/tours/{tour['id']}", json={"title": "Benim"})
        assert response.status_code == 403

    async def test_a_tour_can_be_deleted(
        self, admin_client: AsyncClient, session: AsyncSession
    ) -> None:
        tour = await create(admin_client)
        assert (await admin_client.delete(f"/tours/{tour['id']}")).status_code == 204
        assert await session.get(Tour, uuid.UUID(tour["id"])) is None

    async def test_deleting_a_tour_removes_its_departures(
        self, admin_client: AsyncClient, tour: Tour
    ) -> None:
        """The departure cascade is delete-orphan; nothing may be left behind."""
        created = await admin_client.post(
            "/tour-departures",
            json={
                "tour_id": str(tour.id),
                "start_date": "2030-06-01",
                "end_date": "2030-06-03",
                "price": 100.0,
                "total_quota": 10,
            },
        )
        assert created.status_code == 201, created.text
        departure_id = created.json()["id"]

        assert (await admin_client.delete(f"/tours/{tour.id}")).status_code == 204
        assert (await admin_client.get(f"/tour-departures/{departure_id}")).status_code == 404

    async def test_an_ordinary_user_cannot_delete(
        self, admin_client: AsyncClient, customer_client: AsyncClient
    ) -> None:
        tour = await create(admin_client)
        assert (await customer_client.delete(f"/tours/{tour['id']}")).status_code == 403

    async def test_an_unknown_tour_is_a_404(self, admin_client: AsyncClient) -> None:
        assert (await admin_client.delete(f"/tours/{uuid.uuid4()}")).status_code == 404
