"""Registration, login, password reset and session revocation.

The rest of the suite mints tokens for fixture accounts directly, so nothing
there touches password hashing or the login and reset flows. These tests go
through the real endpoints instead.

The reset token is read out of the mock email the way a user would read it out
of their inbox — `send_email` logs the message body in development — so the
tests do not depend on how the token happens to be minted.
"""

import logging
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import User

# Generated rather than written out: a hard-coded credential-shaped literal is
# exactly what the gitleaks hook is meant to stop, and it is right to flag one
# even in a test. Only the length matters (the schema requires 12+).
PASSWORD = f"pw-{uuid.uuid4().hex}"
NEW_PASSWORD = f"pw-{uuid.uuid4().hex}"
WRONG_PASSWORD = f"pw-{uuid.uuid4().hex}"
THIRD_PASSWORD = f"pw-{uuid.uuid4().hex}"


def unique_email(prefix: str = "kayit") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


async def register(client: AsyncClient, email: str, password: str = PASSWORD) -> dict[str, Any]:
    response = await client.post(
        "/users", json={"email": email, "full_name": "Test Kullanıcı", "password": password}
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def login(client: AsyncClient, email: str, password: str = PASSWORD) -> Any:
    return await client.post("/auth/login", json={"email": email, "password": password})


async def reset_token_from_email(
    client: AsyncClient, email: str, caplog: pytest.LogCaptureFixture
) -> str:
    """Trigger forgot-password and read the token out of the mock email."""
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="armonitex.email"):
        response = await client.post("/auth/forgot-password", json={"email": email})
    assert response.status_code == 200, response.text
    match = re.search(r"token=([\w.\-]+)", caplog.text)
    assert match, f"no reset link in the sent email:\n{caplog.text}"
    return match.group(1)


class TestRegistration:
    async def test_an_account_is_created_without_echoing_the_password(
        self, client: AsyncClient
    ) -> None:
        email = unique_email()
        body = await register(client, email)

        assert body["email"] == email
        assert body["is_active"] is True
        assert body["is_superuser"] is False
        assert "password" not in body
        assert "hashed_password" not in body

    async def test_the_password_is_not_stored_in_the_clear(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        email = unique_email()
        created = await register(client, email)

        stored = await session.get(User, uuid.UUID(created["id"]))
        assert stored is not None
        assert stored.hashed_password != PASSWORD
        assert PASSWORD not in stored.hashed_password
        assert stored.hashed_password.startswith("$argon2")

    async def test_a_duplicate_email_is_a_conflict(self, client: AsyncClient) -> None:
        email = unique_email()
        await register(client, email)
        response = await client.post(
            "/users", json={"email": email, "full_name": "Yine Ben", "password": PASSWORD}
        )
        assert response.status_code == 409

    async def test_a_duplicate_email_in_another_case_is_a_conflict(
        self, client: AsyncClient
    ) -> None:
        """Registration casefolds, so Ali@x and ali@x are the same account."""
        email = unique_email()
        await register(client, email)
        response = await client.post(
            "/users",
            json={"email": email.upper(), "full_name": "Büyük Harf", "password": PASSWORD},
        )
        assert response.status_code == 409

    @pytest.mark.parametrize(
        "payload",
        [
            {"email": "kisa@example.com", "password": "kisa"},
            {"email": "not-an-email", "password": PASSWORD},
            {"email": "eksik@example.com"},
        ],
    )
    async def test_invalid_payloads_are_rejected(
        self, client: AsyncClient, payload: dict[str, str]
    ) -> None:
        response = await client.post("/users", json=payload)
        assert response.status_code == 422


class TestLogin:
    async def test_correct_credentials_return_a_usable_token(self, client: AsyncClient) -> None:
        email = unique_email()
        created = await register(client, email)

        response = await login(client, email)
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert response.json()["token_type"] == "bearer"

        me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["id"] == created["id"]

    async def test_the_oauth2_form_endpoint_also_works(self, client: AsyncClient) -> None:
        email = unique_email()
        await register(client, email)

        response = await client.post("/auth/token", data={"username": email, "password": PASSWORD})
        assert response.status_code == 200
        assert response.json()["access_token"]

    async def test_a_wrong_password_is_rejected(self, client: AsyncClient) -> None:
        email = unique_email()
        await register(client, email)
        response = await login(client, email, password=WRONG_PASSWORD)
        assert response.status_code == 401

    async def test_an_unknown_email_is_rejected(self, client: AsyncClient) -> None:
        response = await login(client, unique_email("yok"))
        assert response.status_code == 401

    async def test_the_email_is_case_insensitive(self, client: AsyncClient) -> None:
        email = unique_email()
        await register(client, email)
        response = await login(client, email.upper())
        assert response.status_code == 200

    async def test_a_deactivated_account_cannot_log_in(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        email = unique_email()
        created = await register(client, email)

        user = await session.get(User, uuid.UUID(created["id"]))
        assert user is not None
        user.is_active = False
        await session.commit()

        assert (await login(client, email)).status_code == 401

    async def test_a_token_stops_working_once_the_account_is_deactivated(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        email = unique_email()
        created = await register(client, email)
        token = (await login(client, email)).json()["access_token"]

        user = await session.get(User, uuid.UUID(created["id"]))
        assert user is not None
        user.is_active = False
        await session.commit()

        me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 401


class TestCurrentUser:
    async def test_me_requires_a_token(self, client: AsyncClient) -> None:
        assert (await client.get("/users/me")).status_code == 401

    @pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b.c"])
    async def test_a_broken_token_is_refused(self, client: AsyncClient, token: str) -> None:
        response = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


class TestForgotPassword:
    async def test_an_unknown_email_gets_the_same_answer(self, client: AsyncClient) -> None:
        """The reply must not reveal whether the address is registered."""
        known = unique_email()
        await register(client, known)

        for_known = await client.post("/auth/forgot-password", json={"email": known})
        for_unknown = await client.post(
            "/auth/forgot-password", json={"email": unique_email("yok")}
        )

        assert for_known.status_code == for_unknown.status_code == 200
        assert for_known.json() == for_unknown.json()

    async def test_no_mail_is_sent_for_an_unknown_address(
        self, client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="armonitex.email"):
            await client.post("/auth/forgot-password", json={"email": unique_email("yok")})
        assert "token=" not in caplog.text


class TestResetPassword:
    async def test_the_emailed_link_changes_the_password(
        self, client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        email = unique_email()
        await register(client, email)
        token = await reset_token_from_email(client, email, caplog)

        response = await client.post(
            "/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD}
        )
        assert response.status_code == 200

        assert (await login(client, email, password=PASSWORD)).status_code == 401
        assert (await login(client, email, password=NEW_PASSWORD)).status_code == 200

    @pytest.mark.parametrize("token", ["not-a-jwt", "a.b.c"])
    async def test_a_broken_token_is_refused(self, client: AsyncClient, token: str) -> None:
        response = await client.post(
            "/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD}
        )
        assert response.status_code == 400

    async def test_a_short_new_password_is_refused(
        self, client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        email = unique_email()
        await register(client, email)
        token = await reset_token_from_email(client, email, caplog)

        response = await client.post(
            "/auth/reset-password", json={"token": token, "new_password": "kisa"}
        )
        assert response.status_code == 422

    async def test_a_reset_link_cannot_be_used_twice(
        self, client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Whoever sees the mail later must not be able to take the account.

        Reset mail sits in an inbox, in mail server logs and in browser history
        long after it is used, so a link that still works is a standing key to
        the account.
        """
        email = unique_email()
        await register(client, email)
        token = await reset_token_from_email(client, email, caplog)

        first = await client.post(
            "/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD}
        )
        assert first.status_code == 200

        second = await client.post(
            "/auth/reset-password", json={"token": token, "new_password": THIRD_PASSWORD}
        )
        assert second.status_code == 400
        assert (await login(client, email, password=NEW_PASSWORD)).status_code == 200

    async def test_a_reset_link_is_not_also_a_session_key(
        self, client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Leaking the mail must not hand over the whole account.

        If the emailed token is an ordinary access token, anyone who reads the
        message can call the API as that user without ever resetting anything.
        """
        email = unique_email()
        await register(client, email)
        token = await reset_token_from_email(client, email, caplog)

        me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 401

    async def test_a_login_token_cannot_reset_a_password(self, client: AsyncClient) -> None:
        """A stolen session token must not be enough to change the password.

        Otherwise any leaked token escalates straight to account takeover: the
        attacker sets a new password and locks the owner out.
        """
        email = unique_email()
        await register(client, email)
        session_token = (await login(client, email)).json()["access_token"]

        response = await client.post(
            "/auth/reset-password",
            json={"token": session_token, "new_password": NEW_PASSWORD},
        )
        assert response.status_code == 400
        assert (await login(client, email, password=PASSWORD)).status_code == 200


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestSessionRevocation:
    """Taking a token back.

    Access tokens are signed blobs the server keeps no record of, so until now
    a leaked one stayed usable for its whole lifetime and there was nothing
    anybody — the owner or an administrator — could do about it. These tests
    pin down that it can now be recalled, and that recalling it does not take
    the account away with it.
    """

    async def test_a_token_is_dead_after_logging_out_everywhere(self, client: AsyncClient) -> None:
        email = unique_email()
        await register(client, email)
        token = (await login(client, email)).json()["access_token"]
        assert (await client.get("/users/me", headers=bearer(token))).status_code == 200

        response = await client.post("/auth/logout-all", headers=bearer(token))
        assert response.status_code == 204

        assert (await client.get("/users/me", headers=bearer(token))).status_code == 401

    async def test_every_device_is_signed_out_not_just_the_caller(
        self, client: AsyncClient
    ) -> None:
        """The point of the endpoint: the leaked copy is the one you cannot reach."""
        email = unique_email()
        await register(client, email)
        phone = (await login(client, email)).json()["access_token"]
        laptop = (await login(client, email)).json()["access_token"]
        assert phone != laptop

        assert (await client.post("/auth/logout-all", headers=bearer(phone))).status_code == 204

        assert (await client.get("/users/me", headers=bearer(laptop))).status_code == 401

    async def test_the_account_still_works_afterwards(self, client: AsyncClient) -> None:
        """Revocation ends sessions; it must not lock the owner out."""
        email = unique_email()
        await register(client, email)
        old = (await login(client, email)).json()["access_token"]
        await client.post("/auth/logout-all", headers=bearer(old))

        fresh = await login(client, email)
        assert fresh.status_code == 200
        new_token = fresh.json()["access_token"]
        assert (await client.get("/users/me", headers=bearer(new_token))).status_code == 200

    async def test_one_account_signing_out_leaves_others_alone(self, client: AsyncClient) -> None:
        mine, theirs = unique_email(), unique_email()
        await register(client, mine)
        await register(client, theirs)
        my_token = (await login(client, mine)).json()["access_token"]
        their_token = (await login(client, theirs)).json()["access_token"]

        assert (await client.post("/auth/logout-all", headers=bearer(my_token))).status_code == 204

        assert (await client.get("/users/me", headers=bearer(their_token))).status_code == 200

    async def test_signing_out_everywhere_requires_a_token(self, client: AsyncClient) -> None:
        assert (await client.post("/auth/logout-all")).status_code == 401

    async def test_a_token_with_no_version_claim_is_refused(
        self, client: AsyncClient, customer: User
    ) -> None:
        """Tokens minted before revocation existed cannot be exempt from it.

        Treating a missing claim as "matches any version" would be the easy way
        to avoid signing everyone out on deploy, and it would leave precisely
        the tokens we cannot recall valid forever.
        """
        settings = get_settings()
        legacy = jwt.encode(
            {
                "sub": str(customer.id),
                "type": "access",
                "exp": datetime.now(UTC) + timedelta(minutes=5),
            },
            settings.jwt_secret_key.get_secret_value(),
            algorithm=settings.jwt_algorithm,
        )

        assert (await client.get("/users/me", headers=bearer(legacy))).status_code == 401

    async def test_resetting_the_password_ends_existing_sessions(
        self, client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The takeover case.

        Somebody with a stolen token is already signed in. The owner notices,
        resets their password — and if the old session survived that, the reset
        would have accomplished nothing beyond changing how the thief would
        have logged in had they needed to.
        """
        email = unique_email()
        await register(client, email)
        stolen = (await login(client, email)).json()["access_token"]
        assert (await client.get("/users/me", headers=bearer(stolen))).status_code == 200

        token = await reset_token_from_email(client, email, caplog)
        reset = await client.post(
            "/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD}
        )
        assert reset.status_code == 200

        assert (await client.get("/users/me", headers=bearer(stolen))).status_code == 401

    async def test_an_admin_can_sign_a_user_out_without_suspending_them(
        self, client: AsyncClient, admin_client: AsyncClient
    ) -> None:
        email = unique_email()
        created = await register(client, email)
        token = (await login(client, email)).json()["access_token"]

        response = await admin_client.post(f"/admin/users/{created['id']}/revoke-sessions")
        assert response.status_code == 200, response.text
        assert response.json()["is_active"] is True

        assert (await client.get("/users/me", headers=bearer(token))).status_code == 401
        assert (await login(client, email)).status_code == 200

    async def test_revoking_sessions_needs_administrator_rights(
        self, client: AsyncClient, customer_client: AsyncClient
    ) -> None:
        created = await register(client, unique_email())
        response = await customer_client.post(f"/admin/users/{created['id']}/revoke-sessions")
        assert response.status_code == 403

    async def test_revoking_sessions_for_an_unknown_user_is_a_404(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.post(f"/admin/users/{uuid.uuid4()}/revoke-sessions")
        assert response.status_code == 404

    async def test_reactivating_an_account_does_not_revive_its_old_tokens(
        self, client: AsyncClient, admin_client: AsyncClient
    ) -> None:
        """Suspending somebody has to be more than a pause.

        `is_active` is read fresh on every request, so a suspended account's
        tokens bounce — but they come straight back to life the moment the
        account is re-enabled, which would hand access back to whoever caused
        the suspension in the first place.
        """
        email = unique_email()
        created = await register(client, email)
        token = (await login(client, email)).json()["access_token"]

        suspend = await admin_client.patch(
            f"/admin/users/{created['id']}", json={"is_active": False}
        )
        assert suspend.status_code == 200, suspend.text
        restore = await admin_client.patch(
            f"/admin/users/{created['id']}", json={"is_active": True}
        )
        assert restore.status_code == 200, restore.text

        assert (await client.get("/users/me", headers=bearer(token))).status_code == 401
