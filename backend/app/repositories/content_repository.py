import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Content

# The class below defines a method called `list`, which shadows the builtin for
# every annotation written after it in the class body. Binding the alias out here,
# at module scope, keeps it meaning the type.
ContentPage = tuple[list[Content], int]


class ContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, content_id: uuid.UUID) -> Content | None:
        return await self._session.get(Content, content_id)

    async def list(self, offset: int, limit: int) -> ContentPage:
        result = await self._session.execute(
            select(Content).order_by(Content.created_at.desc()).offset(offset).limit(limit)
        )
        total = await self._session.scalar(select(func.count()).select_from(Content))
        return list(result.scalars()), total or 0

    async def list_published(self, offset: int, limit: int) -> ContentPage:
        """Published items only, filtered in SQL.

        The public route used to take the first page of *all* content and drop
        the unpublished rows afterwards, so a hundred drafts were enough to push
        every published item off the site.
        """
        published = Content.is_published.is_(True)
        result = await self._session.execute(
            select(Content)
            .where(published)
            .order_by(Content.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        total = await self._session.scalar(
            select(func.count()).select_from(Content).where(published)
        )
        return list(result.scalars()), total or 0

    def add(self, content: Content) -> None:
        self._session.add(content)

    async def delete(self, content: Content) -> None:
        await self._session.delete(content)
