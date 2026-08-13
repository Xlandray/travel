"""Contract tests for content items, admin and public."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Content, User


def unique_slug(prefix: str = "yazi") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


async def create(admin_client: AsyncClient, **rest: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": "Kapadokya Rehberi",
        "slug": unique_slug(),
        "body": "Balonlar gün doğumunda kalkar.",
    }
    payload.update(rest)
    response = await admin_client.post("/admin/contents", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


class TestAdminCrud:
    async def test_a_content_item_round_trips(
        self, admin_client: AsyncClient, superuser: User
    ) -> None:
        created = await create(admin_client)
        assert created["is_published"] is False
        assert created["author_id"] == str(superuser.id)

        fetched = await admin_client.get(f"/admin/contents/{created['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["slug"] == created["slug"]

    async def test_a_duplicate_slug_is_a_conflict(self, admin_client: AsyncClient) -> None:
        first = await create(admin_client)
        response = await admin_client.post(
            "/admin/contents",
            json={"title": "Başka", "slug": first["slug"], "body": "metin"},
        )
        assert response.status_code == 409

    async def test_it_can_be_published_and_unpublished(self, admin_client: AsyncClient) -> None:
        created = await create(admin_client)
        on = await admin_client.patch(
            f"/admin/contents/{created['id']}", json={"is_published": True}
        )
        assert on.status_code == 200
        assert on.json()["is_published"] is True

        off = await admin_client.patch(
            f"/admin/contents/{created['id']}", json={"is_published": False}
        )
        assert off.json()["is_published"] is False

    async def test_it_can_be_deleted(self, admin_client: AsyncClient) -> None:
        created = await create(admin_client)
        assert (await admin_client.delete(f"/admin/contents/{created['id']}")).status_code == 204
        assert (await admin_client.get(f"/admin/contents/{created['id']}")).status_code == 404

    @pytest.mark.parametrize(
        "payload",
        [
            {"title": "", "slug": "gecerli", "body": "x"},
            {"title": "Başlık", "slug": "Gecersiz Slug", "body": "x"},
            {"title": "Başlık", "slug": "gecerli", "body": ""},
            {"title": "Başlık", "slug": "gecerli", "body": "x", "surprise": 1},
        ],
    )
    async def test_invalid_payloads_are_rejected(
        self, admin_client: AsyncClient, payload: dict[str, Any]
    ) -> None:
        assert (await admin_client.post("/admin/contents", json=payload)).status_code == 422

    async def test_an_unknown_item_is_a_404(self, admin_client: AsyncClient) -> None:
        assert (await admin_client.get(f"/admin/contents/{uuid.uuid4()}")).status_code == 404

    async def test_paging_returns_the_refine_shape(self, admin_client: AsyncClient) -> None:
        await create(admin_client)
        response = await admin_client.get("/admin/contents", params={"page": 1, "page_size": 10})
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)
        assert body["total"] >= 1


class TestAuthorization:
    async def test_an_ordinary_user_cannot_list(self, customer_client: AsyncClient) -> None:
        assert (await customer_client.get("/admin/contents")).status_code == 403

    async def test_an_ordinary_user_cannot_create(self, customer_client: AsyncClient) -> None:
        response = await customer_client.post(
            "/admin/contents", json={"title": "X", "slug": unique_slug(), "body": "y"}
        )
        assert response.status_code == 403

    async def test_anonymous_callers_cannot_list(self, client: AsyncClient) -> None:
        assert (await client.get("/admin/contents")).status_code == 401


class TestPublic:
    async def test_only_published_items_are_public(
        self, admin_client: AsyncClient, client: AsyncClient
    ) -> None:
        draft = await create(admin_client)
        live = await create(admin_client, is_published=True)

        body = (await client.get("/contents")).json()

        slugs = [c["slug"] for c in body]
        assert live["slug"] in slugs
        assert draft["slug"] not in slugs

    async def test_a_published_item_is_not_lost_behind_a_page_of_drafts(
        self, client: AsyncClient, session: AsyncSession, superuser: User
    ) -> None:
        """The public list filtered after paging, not in the query.

        It fetched the first hundred rows and then dropped the unpublished ones,
        so once there were a hundred drafts a published item simply stopped being
        published as far as the site was concerned.
        """
        session.add_all(
            Content(
                title=f"Taslak {index}",
                slug=unique_slug("taslak"),
                body="x",
                is_published=False,
                author_id=superuser.id,
            )
            for index in range(120)
        )
        live_slug = unique_slug("yayin")
        session.add(
            Content(
                title="Yayındaki",
                slug=live_slug,
                body="x",
                is_published=True,
                author_id=superuser.id,
            )
        )
        await session.commit()

        body = (await client.get("/contents")).json()

        assert live_slug in [c["slug"] for c in body]

    async def test_the_public_list_needs_no_token(self, client: AsyncClient) -> None:
        assert (await client.get("/contents")).status_code == 200
