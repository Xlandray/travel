"""Contract tests for the tour category endpoints."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tour import Tour, TourCategory


async def create(admin_client: AsyncClient, **payload: Any) -> dict[str, Any]:
    payload.setdefault("name", f"Kategori {uuid.uuid4().hex[:6]}")
    response = await admin_client.post("/tour-categories", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


class TestCreate:
    async def test_the_slug_is_derived_from_the_name(self, admin_client: AsyncClient) -> None:
        category = await create(admin_client, name="Yurt İçi Turlar")
        assert category["slug"] == "yurt-ici-turlar"

    async def test_an_explicit_slug_is_kept(self, admin_client: AsyncClient) -> None:
        category = await create(admin_client, name="Balayı", slug="honeymoon")
        assert category["slug"] == "honeymoon"

    async def test_a_name_with_no_slugable_characters_is_rejected(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.post("/tour-categories", json={"name": "!!! ###"})
        assert response.status_code == 422

    async def test_a_duplicate_slug_conflicts(self, admin_client: AsyncClient) -> None:
        await create(admin_client, name="Kültür Turları")
        response = await admin_client.post("/tour-categories", json={"name": "Kültür Turları"})
        assert response.status_code == 409

    async def test_an_ordinary_user_cannot_create(self, customer_client: AsyncClient) -> None:
        response = await customer_client.post("/tour-categories", json={"name": "Gizli"})
        assert response.status_code == 403

    async def test_anonymous_callers_cannot_create(self, client: AsyncClient) -> None:
        assert (await client.post("/tour-categories", json={"name": "Gizli"})).status_code == 401


class TestList:
    async def test_the_public_list_is_an_array(self, admin_client: AsyncClient) -> None:
        await create(admin_client)
        response = await admin_client.get("/tour-categories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_paging_returns_the_refine_shape(self, admin_client: AsyncClient) -> None:
        await create(admin_client)
        response = await admin_client.get("/tour-categories", params={"page": 1, "page_size": 10})
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)
        assert body["total"] >= 1

    async def test_the_public_list_hides_deactivated_categories(
        self, admin_client: AsyncClient, client: AsyncClient
    ) -> None:
        hidden = await create(admin_client, name="Gizli Kategori", is_active=False)
        response = await client.get("/tour-categories")
        assert response.status_code == 200
        assert hidden["id"] not in [c["id"] for c in response.json()]

    async def test_an_admin_can_still_see_a_deactivated_category(
        self, admin_client: AsyncClient
    ) -> None:
        """Otherwise deactivating one hides it from the only page that can undo it.

        The admin table even renders an Aktif/Pasif tag, so it expects both — but
        the list it reads never contained a passive row.
        """
        hidden = await create(admin_client, name="Gizli Kategori", is_active=False)

        response = await admin_client.get(
            "/tour-categories", params={"page": 1, "page_size": 50, "include_inactive": True}
        )

        assert response.status_code == 200
        assert hidden["id"] in [c["id"] for c in response.json()["data"]]

    async def test_an_ordinary_user_cannot_ask_for_the_hidden_ones(
        self, customer_client: AsyncClient
    ) -> None:
        response = await customer_client.get("/tour-categories", params={"include_inactive": True})
        assert response.status_code == 403

    async def test_anonymous_callers_cannot_ask_for_the_hidden_ones(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/tour-categories", params={"include_inactive": True})
        assert response.status_code in (401, 403)


class TestUpdate:
    async def test_the_name_can_be_changed(self, admin_client: AsyncClient) -> None:
        category = await create(admin_client)
        response = await admin_client.patch(
            f"/tour-categories/{category['id']}", json={"name": "Yeni Ad"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Yeni Ad"

    async def test_a_category_can_be_reactivated(self, admin_client: AsyncClient) -> None:
        category = await create(admin_client, is_active=False)
        response = await admin_client.patch(
            f"/tour-categories/{category['id']}", json={"is_active": True}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True

    async def test_taking_another_categorys_slug_is_a_conflict(
        self, admin_client: AsyncClient
    ) -> None:
        first = await create(admin_client)
        second = await create(admin_client)
        response = await admin_client.patch(
            f"/tour-categories/{second['id']}", json={"slug": first["slug"]}
        )
        assert response.status_code == 409

    async def test_resending_its_own_slug_is_not_a_conflict(
        self, admin_client: AsyncClient
    ) -> None:
        category = await create(admin_client)
        response = await admin_client.patch(
            f"/tour-categories/{category['id']}", json={"slug": category["slug"]}
        )
        assert response.status_code == 200

    async def test_an_unknown_category_is_a_404(self, admin_client: AsyncClient) -> None:
        response = await admin_client.patch(f"/tour-categories/{uuid.uuid4()}", json={"name": "X"})
        assert response.status_code == 404

    async def test_an_ordinary_user_cannot_update(
        self, admin_client: AsyncClient, customer_client: AsyncClient
    ) -> None:
        category = await create(admin_client)
        response = await customer_client.patch(
            f"/tour-categories/{category['id']}", json={"name": "Ele geçirdim"}
        )
        assert response.status_code == 403


class TestDelete:
    async def test_an_empty_category_can_be_deleted(self, admin_client: AsyncClient) -> None:
        category = await create(admin_client)
        assert (await admin_client.delete(f"/tour-categories/{category['id']}")).status_code == 204

    async def test_deleting_a_category_keeps_its_tours(
        self, admin_client: AsyncClient, session: AsyncSession, tour: Tour
    ) -> None:
        """The FK is ON DELETE SET NULL: the tours survive, uncategorised."""
        category = await create(admin_client)
        tour.category_id = uuid.UUID(category["id"])
        await session.commit()

        response = await admin_client.delete(f"/tour-categories/{category['id']}")
        assert response.status_code == 204

        await session.refresh(tour)
        assert tour.category_id is None

        gone = await session.execute(
            select(TourCategory).where(TourCategory.id == uuid.UUID(category["id"]))
        )
        assert gone.scalar_one_or_none() is None

    async def test_an_unknown_category_is_a_404(self, admin_client: AsyncClient) -> None:
        assert (await admin_client.delete(f"/tour-categories/{uuid.uuid4()}")).status_code == 404

    @pytest.mark.parametrize("method", ["delete"])
    async def test_an_ordinary_user_cannot_delete(
        self, admin_client: AsyncClient, customer_client: AsyncClient, method: str
    ) -> None:
        category = await create(admin_client)
        response = await customer_client.request(
            method.upper(), f"/tour-categories/{category['id']}"
        )
        assert response.status_code == 403
