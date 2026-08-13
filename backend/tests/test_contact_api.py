"""Contract tests for the public contact form.

This endpoint takes anonymous input and turns it straight into an email, so what
matters is that nothing a stranger types can reach the mail layer in a shape it
cannot handle.
"""

import logging

import pytest
from httpx import AsyncClient

VALID = {
    "full_name": "Ayşe Yılmaz",
    "email": "ayse@example.com",
    "message": "Kapadokya turu hakkında bilgi almak istiyorum.",
}


class TestSubmit:
    async def test_a_valid_message_is_accepted(self, client: AsyncClient) -> None:
        response = await client.post("/contact", json=VALID)
        assert response.status_code == 201, response.text
        assert response.json()["status"] == "success"

    async def test_the_message_reaches_the_mail_layer(
        self, client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="armonitex.email"):
            response = await client.post("/contact", json=VALID)
        assert response.status_code == 201
        assert VALID["message"] in caplog.text
        assert VALID["email"] in caplog.text

    @pytest.mark.parametrize(
        "payload",
        [
            {**VALID, "email": "not-an-email"},
            {**VALID, "full_name": ""},
            {**VALID, "message": ""},
            {"full_name": "Ayşe", "email": "ayse@example.com"},
            {**VALID, "surprise": "extra"},
        ],
    )
    async def test_invalid_payloads_are_rejected(
        self, client: AsyncClient, payload: dict[str, str]
    ) -> None:
        response = await client.post("/contact", json=payload)
        assert response.status_code == 422

    @pytest.mark.parametrize("name", ["Ali\nBcc: kurban@example.com", "Ali\rX: y", "Ali\r\nX: y"])
    async def test_a_name_with_line_breaks_is_rejected_not_a_500(
        self, client: AsyncClient, name: str
    ) -> None:
        """`full_name` is interpolated into the Subject header.

        Python's email layer refuses a header value containing a line break —
        correctly, since that is how header injection works — but it does so by
        raising, and nothing here caught it, so a stranger could turn the contact
        form into a 500 by putting a newline in their name. It has to be refused
        as bad input instead.
        """
        response = await client.post("/contact", json={**VALID, "full_name": name})
        assert response.status_code == 422

    async def test_a_long_name_is_rejected(self, client: AsyncClient) -> None:
        response = await client.post("/contact", json={**VALID, "full_name": "a" * 256})
        assert response.status_code == 422
