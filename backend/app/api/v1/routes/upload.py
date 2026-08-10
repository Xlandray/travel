import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

router = APIRouter()

# Directory on filesystem for storing tour media
MEDIA_DIR = Path("media")
TOURS_UPLOAD_DIR = MEDIA_DIR / "tours"
TOURS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _detect_content_type(contents: bytes, declared: str | None) -> str:
    """Detects image content type from magic bytes, falling back to the declared MIME."""
    if contents.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if contents.startswith(b"GIF87a") or contents.startswith(b"GIF89a"):
        return "image/gif"
    if contents.startswith(b"RIFF") and contents[8:12] == b"WEBP":
        return "image/webp"
    # Header-based fallback (may be missing or unreliable on some clients)
    if declared in ALLOWED_IMAGE_TYPES:
        return declared
    return ""


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_tour_image(
    request: Request,
    file: UploadFile = File(...),  # noqa: B008
) -> dict[str, str]:
    """Uploads a tour image, saves it to media/tours, and returns the public URL."""
    # Read file first so we can sniff magic bytes regardless of the declared MIME
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Görsel boyutu 10MB sınırını aşamaz.",
        )
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Boş dosya yüklenemez.",
        )

    content_type = _detect_content_type(contents, file.content_type)
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz dosya formatı. Sadece JPG, PNG, WEBP ve GIF formatları desteklenmektedir.",
        )

    extension_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }
    extension = extension_map[content_type]

    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    target_path = TOURS_UPLOAD_DIR / unique_filename

    with target_path.open("wb") as buffer:
        buffer.write(contents)

    # Construct accessible URL
    base_url = str(request.base_url).rstrip("/")
    media_url = f"{base_url}/media/tours/{unique_filename}"

    return {
        "filename": unique_filename,
        "url": media_url,
        "path": f"/media/tours/{unique_filename}",
    }
