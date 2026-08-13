import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.domain.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    """Registration and authentication policies for users."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def register(self, user_in: UserCreate) -> User:
        email = user_in.email.casefold()
        if await self._users.get_by_email(email):
            raise EmailAlreadyRegisteredError("This email address is already registered.")

        user = User(
            email=email,
            full_name=user_in.full_name,
            hashed_password=hash_password(user_in.password),
        )
        self._users.add(user)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            message = "This email address is already registered."
            raise EmailAlreadyRegisteredError(message) from error

        await self._session.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._users.get_by_email(email.casefold())
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password.")
        if not user.is_active:
            raise InvalidCredentialsError("Invalid email or password.")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self._users.get_by_email(email.casefold())

    async def get_active_user(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError("User is not available.")
        return user
