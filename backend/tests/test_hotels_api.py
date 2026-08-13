"""Contract tests for the hotels endpoints.

Covers the behaviour that was verified by hand while the slug work was done:
resolution by slug or UUID, auto-generated slugs, and the 404/409/422 responses.
"""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient


async def _create(admin_client: AsyncClient, **payload: object) -> dict[str, Any]:
    payload.setdefault("city", "Ürgüp")
    response = await admin_client.post("/hotels", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


class TestSlugGeneration:
    async def test_slug_is_derived_from_the_name_when_omitted(
        self, admin_client: AsyncClient
    ) -> None:
        hotel = await _create(admin_client, name="Dağ & Deniz — Butik")
        assert hotel["slug"] == "dag-deniz-butik"

    async def test_an_explicit_slug_is_kept(self, admin_client: AsyncClient) -> None:
        hotel = await _create(admin_client, name="Cave Hotel", slug="magara-oteli")
        assert hotel["slug"] == "magara-oteli"

    async def test_a_name_with_no_slugable_characters_is_rejected(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.post("/hotels", json={"name": "!!! ###", "city": "Test"})
        assert response.status_code == 422
        assert "slug" in response.json()["detail"].lower()

    async def test_a_duplicate_slug_conflicts(self, admin_client: AsyncClient) -> None:
        await _create(admin_client, name="Cave Hotel & Spa")
        response = await admin_client.post(
            "/hotels", json={"name": "Cave Hotel & Spa", "city": "Ürgüp"}
        )
        assert response.status_code == 409


class TestLookup:
    async def test_a_hotel_is_reachable_by_slug_and_by_uuid(
        self, admin_client: AsyncClient
    ) -> None:
        created = await _create(admin_client, name="Cave Hotel & Spa")

        by_slug = await admin_client.get(f"/hotels/{created['slug']}")
        by_uuid = await admin_client.get(f"/hotels/{created['id']}")

        assert by_slug.status_code == 200
        assert by_uuid.status_code == 200
        assert by_slug.json()["id"] == by_uuid.json()["id"] == created["id"]

    async def test_an_unknown_slug_is_a_404(self, client: AsyncClient) -> None:
        response = await client.get("/hotels/yok-boyle-bir-otel")
        assert response.status_code == 404

    async def test_an_unknown_uuid_is_a_404(self, client: AsyncClient) -> None:
        response = await client.get(f"/hotels/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_a_hotel_with_no_tours_returns_an_empty_list(
        self, admin_client: AsyncClient
    ) -> None:
        created = await _create(admin_client, name="Cave Hotel & Spa")
        response = await admin_client.get(f"/hotels/{created['slug']}/tours")
        assert response.status_code == 200
        assert response.json() == []


class TestUpdateAndDelete:
    @pytest.mark.parametrize("key", ["slug", "id"])
    async def test_a_hotel_can_be_updated_by_either_identifier(
        self, admin_client: AsyncClient, key: str
    ) -> None:
        created = await _create(admin_client, name="Cave Hotel & Spa")
        response = await admin_client.patch(f"/hotels/{created[key]}", json={"star_rating": 5})
        assert response.status_code == 200
        assert response.json()["star_rating"] == 5

    async def test_resending_a_hotels_own_slug_is_not_a_conflict(
        self, admin_client: AsyncClient
    ) -> None:
        """Regression: the availability check used to ignore the hotel's own row."""
        created = await _create(admin_client, name="Cave Hotel & Spa")
        response = await admin_client.patch(
            f"/hotels/{created['slug']}", json={"slug": created["slug"]}
        )
        assert response.status_code == 200

    async def test_taking_another_hotels_slug_is_a_conflict(
        self, admin_client: AsyncClient
    ) -> None:
        first = await _create(admin_client, name="Cave Hotel & Spa")
        second = await _create(admin_client, name="Konak Otel")
        response = await admin_client.patch(
            f"/hotels/{second['slug']}", json={"slug": first["slug"]}
        )
        assert response.status_code == 409

    @pytest.mark.parametrize("key", ["slug", "id"])
    async def test_a_hotel_can_be_deleted_by_either_identifier(
        self, admin_client: AsyncClient, key: str
    ) -> None:
        created = await _create(admin_client, name="Cave Hotel & Spa")
        deleted = await admin_client.delete(f"/hotels/{created[key]}")
        assert deleted.status_code == 204
        assert (await admin_client.get(f"/hotels/{created['id']}")).status_code == 404


class TestListing:
    async def test_the_plain_list_is_an_array(self, admin_client: AsyncClient) -> None:
        await _create(admin_client, name="Cave Hotel & Spa")
        response = await admin_client.get("/hotels")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_paging_returns_the_refine_shape(self, admin_client: AsyncClient) -> None:
        """The admin panel's dataProvider requires {data: [...], total}."""
        await _create(admin_client, name="Cave Hotel & Spa")
        response = await admin_client.get("/hotels", params={"page": 1, "page_size": 10})
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)
        assert body["total"] >= 1


class TestAuthorization:
    @pytest.mark.parametrize(
        ("method", "path"),
        [("post", "/hotels"), ("patch", "/hotels/x"), ("delete", "/hotels/x")],
    )
    async def test_write_endpoints_reject_anonymous_callers(
        self, client: AsyncClient, method: str, path: str
    ) -> None:
        # request() rather than client.delete(), which does not take a body.
        response = await client.request(method.upper(), path, json={"name": "X", "city": "Y"})
        assert response.status_code == 401
