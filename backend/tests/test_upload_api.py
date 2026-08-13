"""Contract tests for the tour image upload endpoint.

Uploads are the one place the API accepts arbitrary bytes from a client, so the
tests are mostly about what it refuses: the wrong format, nothing at all, and
anything over the size cap.
"""

from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from PIL import Image

from app.api.v1.routes.upload import MAX_FILE_SIZE, TOURS_UPLOAD_DIR


def png_bytes(width: int = 1200, height: int = 800, colour: str = "red") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, format="PNG")
    return buffer.getvalue()


def upload_file(content: bytes, name: str = "foto.png", mime: str = "image/png") -> dict[str, Any]:
    return {"file": (name, content, mime)}


class TestAuthorization:
    async def test_anonymous_callers_are_refused(self, client: AsyncClient) -> None:
        response = await client.post("/upload", files=upload_file(png_bytes()))
        assert response.status_code == 401

    async def test_an_ordinary_user_is_refused(self, customer_client: AsyncClient) -> None:
        response = await customer_client.post("/upload", files=upload_file(png_bytes()))
        assert response.status_code == 403


class TestAccepted:
    async def test_an_image_becomes_three_webp_renditions(self, admin_client: AsyncClient) -> None:
        response = await admin_client.post("/upload", files=upload_file(png_bytes()))

        assert response.status_code == 201, response.text
        body = response.json()
        assert set(body["renditions"]) == {"hero", "post", "story"}
        assert all(url.endswith(".webp") for url in body["renditions"].values())
        assert body["path"].startswith("/media/tours/")
        assert body["url"].endswith(".webp")

    async def test_the_renditions_are_written_at_their_declared_sizes(
        self, admin_client: AsyncClient
    ) -> None:
        """A rendition that is not actually cropped is not a rendition."""
        response = await admin_client.post("/upload", files=upload_file(png_bytes()))
        assert response.status_code == 201, response.text
        token = response.json()["filename"]

        expected = {"hero": (1600, 900), "post": (1080, 1080), "story": (1080, 1920)}
        for variant, size in expected.items():
            path = Path(TOURS_UPLOAD_DIR) / f"{token}_{variant}.webp"
            assert path.exists(), f"{variant} was not written"
            with Image.open(path) as written:
                assert written.format == "WEBP"
                assert written.size == size

    async def test_the_declared_mime_type_does_not_have_to_be_right(
        self, admin_client: AsyncClient
    ) -> None:
        """The format is decided by the magic bytes, not by what the client says."""
        response = await admin_client.post(
            "/upload",
            files=upload_file(png_bytes(), name="foto.bin", mime="application/octet-stream"),
        )
        assert response.status_code == 201, response.text

    async def test_two_uploads_do_not_collide(self, admin_client: AsyncClient) -> None:
        first = await admin_client.post("/upload", files=upload_file(png_bytes()))
        second = await admin_client.post("/upload", files=upload_file(png_bytes()))
        assert first.json()["filename"] != second.json()["filename"]


class TestRejected:
    async def test_an_empty_file_is_refused(self, admin_client: AsyncClient) -> None:
        """And says so, rather than blaming the file format."""
        response = await admin_client.post("/upload", files=upload_file(b""))
        assert response.status_code == 400
        assert "Boş dosya" in response.json()["detail"]

    async def test_a_format_outside_the_allow_list_is_refused(
        self, admin_client: AsyncClient
    ) -> None:
        """Pillow opens BMP quite happily; the pipeline still must not accept it.

        Without the allow-list the only thing standing between an upload and the
        media directory is whether Pillow can decode it, which is a much larger
        set than the formats this site serves.
        """
        buffer = BytesIO()
        Image.new("RGB", (64, 64), "blue").save(buffer, format="BMP")

        response = await admin_client.post(
            "/upload", files=upload_file(buffer.getvalue(), name="foto.bmp", mime="image/bmp")
        )

        assert response.status_code == 400
        assert "format" in response.json()["detail"].lower()

    async def test_a_non_image_is_refused(self, admin_client: AsyncClient) -> None:
        response = await admin_client.post(
            "/upload", files=upload_file(b"this is not an image at all", name="notes.txt")
        )
        assert response.status_code == 400

    async def test_claiming_to_be_a_png_does_not_help(self, admin_client: AsyncClient) -> None:
        """A text file with an image content type must still be refused."""
        response = await admin_client.post(
            "/upload", files=upload_file(b"<?php echo 1; ?>", name="shell.png", mime="image/png")
        )
        assert response.status_code == 400

    async def test_a_file_over_the_cap_is_refused(self, admin_client: AsyncClient) -> None:
        oversized = b"\x89PNG\r\n\x1a\n" + b"0" * MAX_FILE_SIZE
        response = await admin_client.post("/upload", files=upload_file(oversized))
        assert response.status_code == 400
        assert "10MB" in response.json()["detail"]

    @pytest.mark.parametrize("payload", [b"\x89PNG\r\n\x1a\n", b"GIF89a", b"RIFF0000WEBP"])
    async def test_a_truncated_image_is_refused_not_crashed(
        self, admin_client: AsyncClient, payload: bytes
    ) -> None:
        """Right magic bytes, no actual image: a 400, never a 500."""
        response = await admin_client.post("/upload", files=upload_file(payload))
        assert response.status_code == 400
