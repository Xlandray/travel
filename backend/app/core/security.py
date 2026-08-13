import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()

ACCESS_TOKEN_TYPE = "access"
PASSWORD_RESET_TOKEN_TYPE = "password_reset"

# Reset links live in inboxes and mail server logs, so they expire faster than a
# session does and are additionally single-use (see `password_reset_fingerprint`).
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def _encode(payload: dict[str, Any], token_type: str, lifetime: timedelta) -> str:
    settings = get_settings()
    body = {**payload, "exp": datetime.now(UTC) + lifetime, "type": token_type}
    return jwt.encode(
        body,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def _decode(token: str, token_type: str) -> dict[str, Any]:
    """Decode a token and refuse it unless it is of exactly the expected type.

    The type claim is what keeps the two kinds of token apart. Without it a
    session token also resets the password (a stolen token becomes an account
    takeover) and a password reset link also acts as a session key (reading the
    email is enough to use the API as that person).
    """
    settings = get_settings()
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    if payload.get("type") != token_type:
        raise jwt.InvalidTokenError(f"Expected a {token_type} token.")
    return payload


def create_access_token(subject: str) -> str:
    settings = get_settings()
    return _encode(
        {"sub": subject},
        ACCESS_TOKEN_TYPE,
        timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )


def decode_access_token(token: str) -> str:
    payload = _decode(token, ACCESS_TOKEN_TYPE)
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise jwt.InvalidTokenError("Invalid access token payload.")
    return subject


def password_reset_fingerprint(hashed_password: str) -> str:
    """A short digest of the stored password hash.

    Carried inside the reset token and re-checked when it is used, so the token
    stops working the moment the password changes. That makes a reset link
    single-use without needing a column to store issued tokens in — the account's
    own state is the record of whether the link has been spent.
    """
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:32]


def create_password_reset_token(subject: str, hashed_password: str) -> str:
    return _encode(
        {"sub": subject, "fp": password_reset_fingerprint(hashed_password)},
        PASSWORD_RESET_TOKEN_TYPE,
        timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )


def decode_password_reset_token(token: str) -> tuple[str, str]:
    """Return (subject, fingerprint); raises `jwt.InvalidTokenError` if malformed."""
    payload = _decode(token, PASSWORD_RESET_TOKEN_TYPE)
    subject = payload.get("sub")
    fingerprint = payload.get("fp")
    if not isinstance(subject, str) or not isinstance(fingerprint, str):
        raise jwt.InvalidTokenError("Invalid password reset token payload.")
    return subject, fingerprint
