import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ResourceConflictError, ResourceNotFoundError
from app.models import Content
from app.repositories.content_repository import ContentPage, ContentRepository
from app.schemas.content import ContentCreate, ContentUpdate


class ContentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._contents = ContentRepository(session)

    async def list(self, page: int, page_size: int) -> ContentPage:
        return await self._contents.list((page - 1) * page_size, page_size)

    async def list_published(self, page: int, page_size: int) -> ContentPage:
        return await self._contents.list_published((page - 1) * page_size, page_size)

    async def get(self, content_id: uuid.UUID) -> Content:
        content = await self._contents.get_by_id(content_id)
        if content is None:
            raise ResourceNotFoundError("Content was not found.")
        return content

    async def create(self, content_in: ContentCreate, author_id: uuid.UUID) -> Content:
        content = Content(author_id=author_id, **content_in.model_dump())
        self._contents.add(content)
        await self._commit(content, "A content item with this slug already exists.")
        return content

    async def update(self, content_id: uuid.UUID, content_in: ContentUpdate) -> Content:
        content = await self.get(content_id)
        for field, value in content_in.model_dump(exclude_unset=True).items():
            setattr(content, field, value)
        await self._commit(content, "A content item with this slug already exists.")
        return content

    async def delete(self, content_id: uuid.UUID) -> None:
        content = await self.get(content_id)
        await self._contents.delete(content)
        await self._session.commit()

    async def _commit(self, content: Content, conflict_message: str) -> None:
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ResourceConflictError(conflict_message) from error
        await self._session.refresh(content)
