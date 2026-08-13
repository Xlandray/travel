import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ResourceConflictError, ResourceNotFoundError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import AdminUserUpdate


class AdminUserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def list(self, page: int, page_size: int) -> tuple[list[User], int]:
        return await self._users.list((page - 1) * page_size, page_size)

    async def get(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError("User was not found.")
        return user

    async def update(self, user_id: uuid.UUID, user_in: AdminUserUpdate) -> User:
        user = await self.get(user_id)
        changes = user_in.model_dump(exclude_unset=True)

        # Demoting or deactivating the last superuser leaves an installation
        # nobody can administer, and no endpoint can grant the privilege back —
        # recovery would mean an UPDATE against the database by hand.
        loses_access = changes.get("is_superuser") is False or changes.get("is_active") is False
        if (
            user.is_superuser
            and user.is_active
            and loses_access
            and await self._active_superuser_count() <= 1
        ):
            raise ResourceConflictError(
                "Son yönetici hesabının yetkisi kaldırılamaz veya pasife alınamaz."
            )

        for field, value in changes.items():
            setattr(user, field, value)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def _active_superuser_count(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.is_superuser.is_(True), User.is_active.is_(True))
        )
        return int(total or 0)
