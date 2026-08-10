"""Image processing pipeline for tour media and social content.

Takes any uploaded image (JPEG/PNG/WebP/GIF/AVIF/HEIC), normalizes it to
WebP and produces multiple standardized renditions:

- ``hero``      16:9  landscape  (customer-site tour cards / detail page)
- ``post``      1:1   square     (Instagram feed post, 1080x1080)
- ``story``     9:16  portrait   (Instagram story, 1080x1920)

The pipeline is deliberately decoupled from the upload endpoint so it can
be reused later for automated social-media post generation without touching
the upload flow.
"""

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

# Rational default renditions. 1080px is the sweet spot for both web hero
# images and Instagram (max upload resolution on the Graph API is 1080x1350).
DEFAULT_RENDITIONS: dict[str, tuple[int, int]] = {
    "hero": (1600, 900),  # 16:9 landscape
    "post": (1080, 1080),  # 1:1 square (Instagram feed)
    "story": (1080, 1920),  # 9:16 portrait (Instagram story)
}

# Pillow needs explicit decoders for exotic inputs (AVIF/HEIC).
PIL_SUPPORTED: set[str] = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/avif"}
# Inputs Pillow cannot open directly without extra codecs (HEIC, raw AVIF).
NON_PIL_INPUTS: set[str] = {"image/heic", "image/heif", "image/avif"}

WEBP_QUALITY = 82

Image.MAX_IMAGE_PIXELS = 120_000_000  # allow up to ~120MP, still guards decompression bombs


@dataclass(frozen=True)
class RenderedImage:
    """A generated rendition: filename stem, format and in-memory bytes."""

    variant: str
    stem: str
    bytes: bytes


def _detect_content_type(contents: bytes, declared: str | None) -> str:
    """Detect image type from magic bytes, falling back to the declared MIME."""
    if contents.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if contents.startswith(b"GIF87a") or contents.startswith(b"GIF89a"):
        return "image/gif"
    if contents.startswith(b"RIFF") and contents[8:12] == b"WEBP":
        return "image/webp"
    if contents.startswith(b"\x00\x00\x00") and b"ftypavif" in contents[:32]:
        return "image/avif"
    if contents.startswith(b"\x00\x00\x00") and (
        b"ftypheic" in contents[:32] or b"ftypheix" in contents[:32] or b"ftypmif1" in contents[:32]
    ):
        return "image/heic"
    if declared in (PIL_SUPPORTED | NON_PIL_INPUTS):
        return declared
    return ""


def _open_image(contents: bytes, content_type: str | None) -> Image.Image:
    """Open an image from raw bytes, normalizing EXIF orientation."""
    try:
        img = Image.open(BytesIO(contents))
        img.load()
    except UnidentifiedImageError as exc:
        raise ValueError(f"Okunamayan görsel verisi ({content_type or 'bilinmeyen'}).") from exc
    # Respect EXIF rotation (phone photos frequently come rotated)
    return ImageOps.exif_transpose(img)


def _webp_bytes(img: Image.Image, quality: int = WEBP_QUALITY) -> bytes:
    """Encode an image to WebP bytes."""
    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=6)
    return buf.getvalue()


def _cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Center-crop + resize to the target aspect ratio (like CSS object-fit: cover)."""
    target_ratio = size[0] / size[1]
    width, height = img.size
    source_ratio = width / height

    if source_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        img = img.crop((left, 0, left + new_width, height))
    elif source_ratio < target_ratio:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        img = img.crop((0, top, width, top + new_height))

    return img.resize(size, Image.Resampling.LANCZOS)


def render_all(
    contents: bytes,
    content_type: str | None,
    renditions: dict[str, tuple[int, int]] | None = None,
) -> list[RenderedImage]:
    """Process raw image bytes into multiple WebP renditions.

    Args:
        contents: raw file bytes.
        content_type: declared MIME type (used only for error messages).
        renditions: ``{variant: (width, height)}`` map; defaults to
            ``DEFAULT_RENDITIONS``.

    Returns:
        A list of :class:`RenderedImage` (one per rendition).
    """
    targets = renditions or DEFAULT_RENDITIONS
    detected = _detect_content_type(contents, content_type)
    if detected not in (PIL_SUPPORTED | NON_PIL_INPUTS):
        raise ValueError(
            "Geçersiz dosya formatı. Sadece JPG, PNG, WEBP, GIF, AVIF ve HEIC "
            "formatları desteklenmektedir."
        )
    img = _open_image(contents, detected)

    rendered: list[RenderedImage] = []
    for variant, size in targets.items():
        cover = _cover(img, size)
        rendered.append(RenderedImage(variant=variant, stem=variant, bytes=_webp_bytes(cover)))
    return rendered


def save_renditions(
    upload_dir: Path,
    token: str,
    renditions: list[RenderedImage],
) -> dict[str, Path]:
    """Persist renditions to ``upload_dir``.

    Files are named ``{token}_{variant}.webp`` (e.g. ``a1b2c3_hero.webp``).
    Returns a mapping of variant name to the saved path.
    """
    saved: dict[str, Path] = {}
    for item in renditions:
        target = upload_dir / f"{token}_{item.stem}.webp"
        target.write_bytes(item.bytes)
        saved[item.variant] = target
        logger.debug("wrote %s (%d bytes)", target.name, len(item.bytes))
    return saved
