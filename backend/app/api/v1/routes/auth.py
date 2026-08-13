import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr, Field

from app.api.deps import CurrentUser, SessionDep
from app.core.email import send_email
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    password_reset_fingerprint,
)
from app.domain.exceptions import InvalidCredentialsError
from app.models import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.base import Schema
from app.services.user_service import UserService

router = APIRouter()


class ForgotPasswordRequest(Schema):
    email: EmailStr


class ResetPasswordRequest(Schema):
    token: str
    new_password: str = Field(min_length=12, max_length=128)


@router.post("/token", response_model=Token, summary="OAuth2 Form Girişi")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    """Exchange valid form credentials for a short-lived OAuth2 bearer token."""
    try:
        user = await UserService(session).authenticate(form_data.username, form_data.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    return Token(access_token=create_access_token(str(user.id), user.token_version))


@router.post("/login", response_model=Token, summary="JSON Giriş Endpoint'i")
async def login_json(
    credentials: LoginRequest,
    session: SessionDep,
) -> Token:
    """Exchange valid JSON credentials for a short-lived OAuth2 bearer token."""
    try:
        user = await UserService(session).authenticate(credentials.email, credentials.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    return Token(access_token=create_access_token(str(user.id), user.token_version))


@router.post("/forgot-password", summary="Şifremi Unuttum")
async def request_password_reset(
    request_in: ForgotPasswordRequest,
    session: SessionDep,
) -> dict[str, str]:
    """Sends a password reset link to user's email if registered."""
    try:
        user = await UserService(session).get_by_email(request_in.email)
        if user:
            reset_token = create_password_reset_token(str(user.id), user.hashed_password)
            reset_url = f"https://armonitex.com.tr/auth/reset-password?token={reset_token}"
            subject = "Armonitex Şifre Sıfırlama Talebi"
            body = (
                f"Merhaba {user.full_name},\n\n"
                f"Hesabınız için şifre sıfırlama talebi alındı.\n"
                f"Aşağıdaki bağlantıyı kullanarak şifrenizi sıfırlayabilirsiniz:\n"
                f"{reset_url}\n\n"
                f"Bu talebi siz yapmadıysanız lütfen bu e-postayı dikkate almayın.\n\n"
                f"Saygılarımızla,\nArmonitex Ekibi"
            )
            await send_email(to_email=user.email, subject=subject, body=body)
    except Exception:
        pass

    return {"message": "Sıfırlama talimatları e-posta adresinize gönderildi."}


@router.post("/reset-password", summary="Şifreyi Token ile Sıfırla")
async def reset_password(
    payload: ResetPasswordRequest,
    session: SessionDep,
) -> dict[str, str]:
    """Reset a user's password using the token emailed by forgot-password.

    Only a `password_reset` token is accepted, and only while it still matches
    the account's current password hash — so a session token cannot change a
    password, and a link that has already been used is dead.
    """
    invalid_link = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Geçersiz veya süresi dolmuş sıfırlama bağlantısı.",
    )

    try:
        subject, fingerprint = decode_password_reset_token(payload.token)
        user_id = uuid.UUID(subject)
    except (jwt.InvalidTokenError, ValueError) as error:
        raise invalid_link from error

    try:
        user = await UserService(session).get_active_user(user_id)
    except InvalidCredentialsError as error:
        raise invalid_link from error

    if fingerprint != password_reset_fingerprint(user.hashed_password):
        raise invalid_link

    # Somebody resetting a password may well be doing it because their account
    # was taken over, so the sessions the attacker holds have to die with the
    # old password — otherwise the reset only changes how they log in next time.
    user.hashed_password = hash_password(payload.new_password)
    user.token_version = User.token_version + 1
    await session.commit()

    return {"message": "Şifreniz başarıyla güncellendi."}


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Tüm Oturumları Kapat",
)
async def logout_all_sessions(current_user: CurrentUser, session: SessionDep) -> None:
    """Revoke every session token for the signed-in account, including this one.

    Signing out normally just forgets the token on the client, which does
    nothing about a copy somebody else has. This is the endpoint to hit when a
    token may have leaked; the caller has to log in again afterwards.
    """
    await UserService(session).revoke_tokens(current_user)
