from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas import ContentRead
from app.services.content_service import ContentService

router = APIRouter()


@router.get("", response_model=list[ContentRead])
async def get_public_contents(session: SessionDep) -> list[ContentRead]:
    """The published content items, newest first.

    Filtering happens in SQL. Taking a page of everything and dropping the
    drafts afterwards meant a hundred unpublished items were enough to empty the
    public list.
    """
    data, _ = await ContentService(session).list_published(page=1, page_size=100)
    return [ContentRead.model_validate(c) for c in data]
