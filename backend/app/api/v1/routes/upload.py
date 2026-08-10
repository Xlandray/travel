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


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_tour_image(
    request: Request,
    file: UploadFile = File(...),  # noqa: B008
) -> dict[str, str]:
    """Uploads a tour image, saves it to media/tours, and returns the public URL."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz dosya formatı. Sadece JPG, PNG, WEBP ve GIF formatları desteklenmektedir.",
        )

    # Determine file extension safely
    filename = file.filename or "image.jpg"
    extension = filename.split(".")[-1].lower() if "." in filename else "jpg"
    if extension not in {"jpg", "jpeg", "png", "webp", "gif"}:
        extension = "jpg"

    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    target_path = TOURS_UPLOAD_DIR / unique_filename

    # Read and save file safely
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Görsel boyutu 10MB sınırını aşamaz.",
        )

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
