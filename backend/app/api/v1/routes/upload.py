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


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_tour_image(
    request: Request,
    _: CurrentSuperuser,
    file: UploadFile = File(...),  # noqa: B008
) -> dict[str, object]:
    """Uploads a tour image, normalizes it to WebP renditions, and returns URLs."""
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
