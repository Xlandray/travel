import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Setting


class SettingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, setting_id: uuid.UUID) -> Setting | None:
        return await self._session.get(Setting, setting_id)

    async def get_all(self) -> list[Setting]:
        result = await self._session.execute(select(Setting).order_by(Setting.key))
        return list(result.scalars())

    async def list(self, offset: int, limit: int) -> tuple[list[Setting], int]:
        result = await self._session.execute(
            select(Setting).order_by(Setting.key).offset(offset).limit(limit)
        )
        total = await self._session.scalar(select(func.count()).select_from(Setting))
        return list(result.scalars()), total or 0

    def add(self, setting: Setting) -> None:
        self._session.add(setting)

    async def delete(self, setting: Setting) -> None:
        await self._session.delete(setting)
