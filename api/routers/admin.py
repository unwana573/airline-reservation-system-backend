from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.deps import require_role
from api.schemas.admin import (
    AirportCreate,
    AirportOut,
    DealAdminOut,
    DealCreate,
    DealUpdate,
    FeaturedDestinationAdminOut,
    FeaturedDestinationCreate,
    FeaturedDestinationUpdate,
)
from api.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin", "super_admin"))])


# ── Airports (powers the From/To fields on the public Book page) ──

@router.get("/airports", response_model=list[AirportOut])
async def list_airports(db: AsyncSession = Depends(get_db)):
    return await admin_service.list_airports(db)


@router.post("/airports", response_model=AirportOut, status_code=201)
async def create_airport(payload: AirportCreate, db: AsyncSession = Depends(get_db)):
    return await admin_service.create_airport(db, payload)


# ── Destinations ──

@router.get("/destinations", response_model=list[FeaturedDestinationAdminOut])
async def list_destinations(db: AsyncSession = Depends(get_db)):
    return await admin_service.list_destinations(db)


@router.post("/destinations", response_model=FeaturedDestinationAdminOut, status_code=201)
async def create_destination(payload: FeaturedDestinationCreate, db: AsyncSession = Depends(get_db)):
    return await admin_service.create_destination(db, payload)


@router.patch("/destinations/{destination_id}", response_model=FeaturedDestinationAdminOut)
async def update_destination(destination_id: int, payload: FeaturedDestinationUpdate, db: AsyncSession = Depends(get_db)):
    return await admin_service.update_destination(db, destination_id, payload)


@router.delete("/destinations/{destination_id}", status_code=204)
async def delete_destination(destination_id: int, db: AsyncSession = Depends(get_db)):
    await admin_service.delete_destination(db, destination_id)


# ── Deals / Popular offers ──

@router.get("/deals", response_model=list[DealAdminOut])
async def list_deals(db: AsyncSession = Depends(get_db)):
    return await admin_service.list_deals(db)


@router.post("/deals", response_model=DealAdminOut, status_code=201)
async def create_deal(payload: DealCreate, db: AsyncSession = Depends(get_db)):
    return await admin_service.create_deal(db, payload)


@router.patch("/deals/{deal_id}", response_model=DealAdminOut)
async def update_deal(deal_id: int, payload: DealUpdate, db: AsyncSession = Depends(get_db)):
    return await admin_service.update_deal(db, deal_id, payload)


@router.delete("/deals/{deal_id}", status_code=204)
async def delete_deal(deal_id: int, db: AsyncSession = Depends(get_db)):
    await admin_service.delete_deal(db, deal_id)