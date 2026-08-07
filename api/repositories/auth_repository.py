import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import OAuthAccount, User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    first_name: str,
    last_name: str,
    password_hash: str | None = None,
    title: str | None = None,
    marketing_opt_in: bool = False,
) -> User:
    user = User(
        email=email,
        password_hash=password_hash,
        title=title,
        first_name=first_name,
        last_name=last_name,
        marketing_opt_in=marketing_opt_in,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(db: AsyncSession, user: User, new_password_hash: str) -> User:
    user.password_hash = new_password_hash
    await db.commit()
    await db.refresh(user)
    return user


async def get_oauth_account(db: AsyncSession, provider: str, provider_user_id: str) -> OAuthAccount | None:
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider, OAuthAccount.provider_user_id == provider_user_id
        )
    )
    return result.scalar_one_or_none()


async def link_oauth_account(db: AsyncSession, user: User, provider: str, provider_user_id: str) -> OAuthAccount:
    account = OAuthAccount(user_id=user.id, provider=provider, provider_user_id=provider_user_id)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account