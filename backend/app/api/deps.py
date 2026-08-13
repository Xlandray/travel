import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_session
from app.domain.exceptions import InvalidCredentialsError
from app.models import User
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        subject, token_version = decode_access_token(token)
        user_id = uuid.UUID(subject)
        return await UserService(session).get_authenticated_user(user_id, token_version)
    except (jwt.PyJWTError, ValueError, InvalidCredentialsError) as error:
        raise credentials_error from error


CurrentUser = Annotated[User, Depends(get_current_user)]

# auto_error=False: no Authorization header is a valid state here, not a 401.
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_optional_user(
    token: Annotated[str | None, Depends(optional_oauth2_scheme)],
    session: SessionDep,
) -> User | None:
    """The signed-in user, or None for anonymous callers.

    For endpoints the public site and the admin panel share, where being signed
    in widens what you may ask for rather than deciding whether you get in.
    A malformed token is treated as anonymous.
    """
    if not token:
        return None
    try:
        subject, token_version = decode_access_token(token)
        return await UserService(session).get_authenticated_user(uuid.UUID(subject), token_version)
    except (jwt.PyJWTError, ValueError, InvalidCredentialsError):
        return None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_current_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required.",
        )
    return current_user


CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
