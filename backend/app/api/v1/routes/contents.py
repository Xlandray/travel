from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas import ContentRead
from app.services.content_service import ContentService

router = APIRouter()


@router.get("", response_model=list[ContentRead])
async def get_public_contents(session: SessionDep) -> list[ContentRead]:
    data, _ = await ContentService(session).list(page=1, page_size=100)
    return [ContentRead.model_validate(c) for c in data if c.is_published]

