from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from api.core.config import get_settings

settings = get_settings()

# Pool sizing args only apply to real connection-pooled backends (e.g. Postgres).
# SQLite (used for lightweight local testing) uses NullPool and rejects these kwargs.
_engine_kwargs = {"echo": settings.debug, "pool_pre_ping": True}
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs.update(pool_size=5, max_overflow=10)

engine = create_async_engine(settings.database_url, **_engine_kwargs)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session per request, always closed after."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()