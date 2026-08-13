import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ResourceConflictError, ResourceNotFoundError
from app.models import Setting
from app.repositories.setting_repository import SettingRepository
from app.schemas.setting import SettingCreate, SettingUpdate


class SettingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._settings = SettingRepository(session)

    async def list(self, page: int, page_size: int) -> tuple[list[Setting], int]:
        return await self._settings.list((page - 1) * page_size, page_size)

    async def get_public(self) -> dict[str, dict[str, Any]]:
        settings = await self._settings.get_all()
        return {setting.key: setting.value for setting in settings}

    async def get(self, setting_id: uuid.UUID) -> Setting:
        setting = await self._settings.get_by_id(setting_id)
        if setting is None:
            raise ResourceNotFoundError("Setting was not found.")
        return setting

    async def create(self, setting_in: SettingCreate) -> Setting:
        setting = Setting(**setting_in.model_dump())
        self._settings.add(setting)
        await self._commit(setting, "A setting with this key already exists.")
        return setting

    async def update(self, setting_id: uuid.UUID, setting_in: SettingUpdate) -> Setting:
        setting = await self.get(setting_id)
        for field, value in setting_in.model_dump(exclude_unset=True).items():
            setattr(setting, field, value)
        await self._commit(setting, "A setting with this key already exists.")
        return setting

    async def delete(self, setting_id: uuid.UUID) -> None:
        setting = await self.get(setting_id)
        await self._settings.delete(setting)
        await self._session.commit()

    async def _commit(self, setting: Setting, conflict_message: str) -> None:
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ResourceConflictError(conflict_message) from error
        await self._session.refresh(setting)
