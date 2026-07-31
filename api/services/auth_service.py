import uuid as uuid_module

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_password_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from api.models import User
from api.repositories import auth_repository
from api.schemas.auth import TokenPair, UserLogin, UserRegister

settings = get_settings()


async def register_user(db: AsyncSession, payload: UserRegister) -> User:
    existing = await auth_repository.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    password_hash = hash_password(payload.password)
    user = await auth_repository.create_user(
        db,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password_hash=password_hash,
        title=payload.title,
        marketing_opt_in=payload.marketing_opt_in,
    )
    return user


async def authenticate_user(db: AsyncSession, payload: UserLogin) -> User:
    user = await auth_repository.get_user_by_email(db, payload.email)
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return user


def issue_token_pair(user: User, remember_me: bool = False) -> TokenPair:
    access = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
    # "Keep me signed in on this device" → longer-lived refresh token.
    # Without it, the refresh token still works but expires sooner (session-like behavior).
    refresh_days = settings.refresh_token_expire_days if remember_me else 1
    refresh = create_refresh_token(subject=str(user.id), expire_days=refresh_days)
    return TokenPair(access_token=access, refresh_token=refresh)


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenPair:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user = await auth_repository.get_user_by_id(db, uuid_module.UUID(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")

    return issue_token_pair(user)


async def request_password_reset(db: AsyncSession, email: str) -> str | None:
    """Returns the reset token if the user exists, else None.

    Always return a generic success message to the caller regardless of the
    result — never reveal whether an email is registered (enumeration risk).
    """
    user = await auth_repository.get_user_by_email(db, email)
    if not user:
        return None
    return create_password_reset_token(str(user.id))


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    try:
        user_id = decode_password_reset_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = await auth_repository.get_user_by_id(db, uuid_module.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User no longer exists")

    new_hash = hash_password(new_password)
    await auth_repository.update_password(db, user, new_hash)


# ── Google OAuth ("Continue with Google") ──

async def authenticate_with_google(db: AsyncSession, google_id_token_str: str) -> User:
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured on this server",
        )

    try:
        claims = google_id_token.verify_oauth2_token(
            google_id_token_str, google_requests.Request(), settings.google_client_id
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential")

    google_user_id = claims["sub"]
    email = claims.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google account has no email")

    existing_link = await auth_repository.get_oauth_account(db, "google", google_user_id)
    if existing_link:
        user = await auth_repository.get_user_by_id(db, existing_link.user_id)
        if user:
            return user

    # No existing OAuth link — attach to a matching email account, or create a new one.
    user = await auth_repository.get_user_by_email(db, email)
    if not user:
        user = await auth_repository.create_user(
            db,
            email=email,
            first_name=claims.get("given_name", ""),
            last_name=claims.get("family_name", ""),
            password_hash=None,  # OAuth-only account, no local password
        )

    await auth_repository.link_oauth_account(db, user, "google", google_user_id)
    return user