"""Contract tests for admin user management."""

import uuid

from httpx import AsyncClient

from app.models import User


class TestRead:
    async def test_paging_returns_the_refine_shape(
        self, admin_client: AsyncClient, customer: User
    ) -> None:
        response = await admin_client.get("/admin/users", params={"page": 1, "page_size": 10})
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)
        assert body["total"] >= 2

    async def test_a_single_user_can_be_read(
        self, admin_client: AsyncClient, customer: User
    ) -> None:
        response = await admin_client.get(f"/admin/users/{customer.id}")
        assert response.status_code == 200
        assert response.json()["email"] == customer.email

    async def test_no_password_material_is_returned(
        self, admin_client: AsyncClient, customer: User
    ) -> None:
        body = (await admin_client.get(f"/admin/users/{customer.id}")).json()
        assert "hashed_password" not in body
        assert "password" not in body

    async def test_an_unknown_user_is_a_404(self, admin_client: AsyncClient) -> None:
        assert (await admin_client.get(f"/admin/users/{uuid.uuid4()}")).status_code == 404


class TestAuthorization:
    async def test_an_ordinary_user_cannot_list(self, customer_client: AsyncClient) -> None:
        assert (await customer_client.get("/admin/users")).status_code == 403

    async def test_an_ordinary_user_cannot_promote_themselves(
        self, customer_client: AsyncClient, customer: User
    ) -> None:
        response = await customer_client.patch(
            f"/admin/users/{customer.id}", json={"is_superuser": True}
        )
        assert response.status_code == 403

    async def test_anonymous_callers_cannot_list(self, client: AsyncClient) -> None:
        assert (await client.get("/admin/users")).status_code == 401


class TestUpdate:
    async def test_a_user_can_be_promoted(self, admin_client: AsyncClient, customer: User) -> None:
        response = await admin_client.patch(
            f"/admin/users/{customer.id}", json={"is_superuser": True}
        )
        assert response.status_code == 200
        assert response.json()["is_superuser"] is True

    async def test_a_user_can_be_deactivated(
        self, admin_client: AsyncClient, customer: User
    ) -> None:
        response = await admin_client.patch(
            f"/admin/users/{customer.id}", json={"is_active": False}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    async def test_the_full_name_can_be_changed(
        self, admin_client: AsyncClient, customer: User
    ) -> None:
        response = await admin_client.patch(
            f"/admin/users/{customer.id}", json={"full_name": "Yeni Ad"}
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Yeni Ad"

    async def test_an_unknown_user_is_a_404(self, admin_client: AsyncClient) -> None:
        response = await admin_client.patch(f"/admin/users/{uuid.uuid4()}", json={"full_name": "X"})
        assert response.status_code == 404


class TestLastSuperuser:
    """Nobody may remove the last way back in.

    Demoting or deactivating the only remaining superuser leaves an installation
    with no account that can administer it, and no endpoint that can grant the
    privilege back — the fix would have to be a manual UPDATE against the
    database.
    """

    async def test_the_last_superuser_cannot_be_demoted(
        self, admin_client: AsyncClient, superuser: User
    ) -> None:
        response = await admin_client.patch(
            f"/admin/users/{superuser.id}", json={"is_superuser": False}
        )
        assert response.status_code == 409

    async def test_the_last_superuser_cannot_be_deactivated(
        self, admin_client: AsyncClient, superuser: User
    ) -> None:
        response = await admin_client.patch(
            f"/admin/users/{superuser.id}", json={"is_active": False}
        )
        assert response.status_code == 409

    async def test_a_superuser_can_be_demoted_once_another_exists(
        self, admin_client: AsyncClient, superuser: User, customer: User
    ) -> None:
        promoted = await admin_client.patch(
            f"/admin/users/{customer.id}", json={"is_superuser": True}
        )
        assert promoted.status_code == 200

        response = await admin_client.patch(
            f"/admin/users/{superuser.id}", json={"is_superuser": False}
        )
        assert response.status_code == 200
        assert response.json()["is_superuser"] is False
