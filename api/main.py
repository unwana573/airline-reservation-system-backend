from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import get_settings
from api.core.init_db import create_tables
from api.routers import auth, seatmaps
from api.routers import flights
import asyncio

from api.core.database import Base, engine
from api import models  # noqa: F401 — imported so its tables register on Base.metadata

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local-dev convenience: creates any tables that don't exist yet.
    # It's a no-op against tables that already exist — safe to run every
    # restart. Only auto-run in debug mode; production should manage
    # schema deliberately (e.g. via Alembic) rather than on every deploy.
    if settings.debug:
        await create_tables()
    yield


app = FastAPI(
    title="Skyra API",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(flights.router, prefix=settings.api_v1_prefix)
app.include_router(seatmaps.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "environment": settings.environment}


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

# uvicorn api.main:app --reload