"""Contract tests for application settings, admin and public."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient


async def create(admin_client: AsyncClient, key: str, **rest: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"key": key, "value": {"deger": "x"}}
    payload.update(rest)
    response = await admin_client.post("/admin/settings", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def unique_key(prefix: str = "test") -> str:
    return f"{prefix}.k{uuid.uuid4().hex[:8]}"


class TestKeys:
    @pytest.mark.parametrize(
        "key",
        [
            "site.iletisim.adres",
            "site.iletisim.telefon",
            "rezervasyon.kapora_yuzde",
            "site.calisma_saatleri",
            "basit",
        ],
    )
    async def test_the_dotted_namespacing_actually_in_use_is_accepted(
        self, admin_client: AsyncClient, key: str
    ) -> None:
        """Every setting the site reads is dot-namespaced.

        The customer footer looks up `site.iletisim.adres`, which no admin could
        ever create while the key pattern refused a dot — so that line of the
        footer was permanently stuck on its hard-coded fallback.
        """
        response = await admin_client.post(
            "/admin/settings", json={"key": key, "value": {"deger": "x"}}
        )
        assert response.status_code == 201, response.text
        assert response.json()["key"] == key

    @pytest.mark.parametrize(
        "key",
        [
            "Site.Iletisim",
            "1site.adres",
            "site..adres",
            "site.",
            ".site",
            "site adres",
            "site/adres",
            "site-adres",
            "",
        ],
    )
    async def test_malformed_keys_are_rejected(self, admin_client: AsyncClient, key: str) -> None:
        response = await admin_client.post(
            "/admin/settings", json={"key": key, "value": {"deger": "x"}}
        )
        assert response.status_code == 422

    async def test_a_duplicate_key_is_a_conflict(self, admin_client: AsyncClient) -> None:
        key = unique_key()
        await create(admin_client, key)
        response = await admin_client.post(
            "/admin/settings", json={"key": key, "value": {"deger": "y"}}
        )
        assert response.status_code == 409


class TestAdminCrud:
    async def test_a_setting_round_trips(self, admin_client: AsyncClient) -> None:
        created = await create(
            admin_client, unique_key(), value={"deger": "0282"}, description="Telefon"
        )
        fetched = await admin_client.get(f"/admin/settings/{created['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["value"] == {"deger": "0282"}
        assert fetched.json()["description"] == "Telefon"

    async def test_the_value_can_be_replaced(self, admin_client: AsyncClient) -> None:
        created = await create(admin_client, unique_key())
        response = await admin_client.patch(
            f"/admin/settings/{created['id']}", json={"value": {"deger": "yeni", "ek": 1}}
        )
        assert response.status_code == 200
        assert response.json()["value"] == {"deger": "yeni", "ek": 1}

    async def test_a_setting_can_be_deleted(self, admin_client: AsyncClient) -> None:
        created = await create(admin_client, unique_key())
        assert (await admin_client.delete(f"/admin/settings/{created['id']}")).status_code == 204
        assert (await admin_client.get(f"/admin/settings/{created['id']}")).status_code == 404

    async def test_paging_returns_the_refine_shape(self, admin_client: AsyncClient) -> None:
        await create(admin_client, unique_key())
        response = await admin_client.get("/admin/settings", params={"page": 1, "page_size": 10})
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)
        assert body["total"] >= 1

    @pytest.mark.parametrize("setting_id", ["00000000-0000-0000-0000-000000000000"])
    async def test_an_unknown_setting_is_a_404(
        self, admin_client: AsyncClient, setting_id: str
    ) -> None:
        assert (await admin_client.get(f"/admin/settings/{setting_id}")).status_code == 404


class TestAuthorization:
    async def test_an_ordinary_user_cannot_read_settings(
        self, customer_client: AsyncClient
    ) -> None:
        assert (await customer_client.get("/admin/settings")).status_code == 403

    async def test_an_ordinary_user_cannot_write_settings(
        self, customer_client: AsyncClient
    ) -> None:
        response = await customer_client.post(
            "/admin/settings", json={"key": unique_key(), "value": {"deger": "x"}}
        )
        assert response.status_code == 403

    async def test_anonymous_callers_cannot_read_settings(self, client: AsyncClient) -> None:
        assert (await client.get("/admin/settings")).status_code == 401


class TestPublicSettings:
    async def test_the_public_map_is_keyed_by_setting_key(
        self, admin_client: AsyncClient, client: AsyncClient
    ) -> None:
        key = unique_key("site")
        await create(admin_client, key, value={"deger": "0282 650 00 00"})

        response = await client.get("/public/settings")

        assert response.status_code == 200
        body = response.json()
        assert body[key] == {"deger": "0282 650 00 00"}

    async def test_the_public_map_exposes_no_ids_or_timestamps(
        self, admin_client: AsyncClient, client: AsyncClient
    ) -> None:
        key = unique_key("site")
        created = await create(admin_client, key)

        body = (await client.get("/public/settings")).json()

        assert body[key] == {"deger": "x"}
        assert created["id"] not in str(body)
        assert "created_at" not in str(body)
