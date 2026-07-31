import asyncio

from api.core.database import Base, engine
from api import models  # noqa: F401 — imported so its tables register on Base.metadata


async def create_tables() -> None:
    """Creates all tables defined in api/models.py directly from SQLAlchemy metadata.

    This is a local-dev convenience — it has no migration history and won't
    alter existing tables if a model changes later (create_all only creates
    tables that don't exist yet). Once the schema stabilizes, switch to
    Alembic migrations (alembic upgrade head) for anything beyond local setup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")


if __name__ == "__main__":
    asyncio.run(create_tables())