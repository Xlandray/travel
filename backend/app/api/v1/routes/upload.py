import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.api.deps import CurrentSuperuser
from app.services.image_pipeline import render_all, save_renditions

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory on filesystem for storing tour media
MEDIA_DIR = Path("media")
TOURS_UPLOAD_DIR = MEDIA_DIR / "tours"
TOURS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
READ_CHUNK = 1024 * 1024


async def _read_capped(file: UploadFile, limit: int) -> bytes:
    """Read at most `limit` bytes, giving up as soon as the cap is passed.

    Reading the whole upload first and checking the length afterwards means a
    caller can make the server hold an arbitrarily large file in memory before
    it is rejected — the size limit only protects what is stored, not what it
    costs to refuse. Stopping at the first chunk past the cap bounds that to
    limit + one chunk.
    """
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(READ_CHUNK):
        total += len(chunk)
        if total > limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Görsel boyutu 10MB sınırını aşamaz.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_tour_image(
    request: Request,
    _: CurrentSuperuser,
    file: UploadFile = File(...),  # noqa: B008
) -> dict[str, object]:
    """Uploads a tour image, normalizes it to WebP renditions, and returns URLs."""
    contents = await _read_capped(file, MAX_FILE_SIZE)
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Boş dosya yüklenemez.",
        )

    try:
        renditions = render_all(contents, file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = uuid.uuid4().hex
    saved = save_renditions(TOURS_UPLOAD_DIR, token, renditions)

    base_url = str(request.base_url).rstrip("/")
    urls = {variant: f"{base_url}/media/tours/{path.name}" for variant, path in saved.items()}
    logger.info("uploaded %s -> %s renditions", file.filename, token)

    return {
        "filename": token,
        "path": f"/media/tours/{saved['hero'].name}",
        "url": urls["hero"],
        "renditions": urls,
    }
