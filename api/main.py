from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import get_settings
from api.routers import booking, content, flights, payment, seatmaps

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is now managed by Alembic migrations (`alembic upgrade head`),
    # not created automatically here — running both would conflict: Alembic
    # would find tables that already exist without a recorded migration
    # history, and "alembic upgrade head" would fail with "relation already
    # exists" on a fresh checkout. Run the migration once before starting
    # the server; see alembic/README or the project setup docs.
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

app.include_router(flights.router, prefix=settings.api_v1_prefix)
app.include_router(seatmaps.router, prefix=settings.api_v1_prefix)
app.include_router(booking.router, prefix=settings.api_v1_prefix)
app.include_router(payment.router, prefix=settings.api_v1_prefix)
app.include_router(content.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "environment": settings.environment}
