"""SUPERSEDED by Alembic migrations (see /alembic).

This still works standalone (`python -m api.core.init_db`) for a quick
throwaway local database, but it has no migration history and won't alter
existing tables if a model changes. Use `alembic upgrade head` for anything
you intend to keep — running this AND Alembic against the same database
will conflict (Alembic will find tables it didn't create and doesn't know
about).
"""

import asyncio

from api.core.database import Base, engine
from api import models  # noqa: F401


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")


if __name__ == "__main__":
    asyncio.run(create_tables())