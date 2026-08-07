from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories import content_repository
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


# ── Airports ──

async def list_airports(db: AsyncSession) -> list[AirportOut]:
    airports = await content_repository.admin_list_airports(db)
    return [AirportOut.model_validate(a) for a in airports]


async def create_airport(db: AsyncSession, payload: AirportCreate) -> AirportOut:
    existing = await content_repository.get_airport_by_iata(db, payload.iata_code.upper())
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An airport with this IATA code already exists")

    airport = await content_repository.admin_create_airport(
        db, iata_code=payload.iata_code.upper(), name=payload.name, city=payload.city, country=payload.country
    )
    return AirportOut.model_validate(airport)


# ── Destinations ──

async def list_destinations(db: AsyncSession) -> list[FeaturedDestinationAdminOut]:
    destinations = await content_repository.admin_list_destinations(db)
    return [FeaturedDestinationAdminOut.model_validate(d) for d in destinations]


async def create_destination(db: AsyncSession, payload: FeaturedDestinationCreate) -> FeaturedDestinationAdminOut:
    airport = await content_repository.get_airport_by_iata(db, payload.airport_iata_code.upper())
    if not airport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No airport found with IATA code {payload.airport_iata_code.upper()} — create the airport first",
        )

    fields = payload.model_dump(exclude={"airport_iata_code"})
    destination = await content_repository.admin_create_destination(db, airport_id=airport.id, **fields)
    return FeaturedDestinationAdminOut.model_validate(destination)


async def update_destination(db: AsyncSession, destination_id: int, payload: FeaturedDestinationUpdate) -> FeaturedDestinationAdminOut:
    destination = await content_repository.admin_get_destination(db, destination_id)
    if not destination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")

    updated = await content_repository.admin_update_destination(db, destination, **payload.model_dump())
    return FeaturedDestinationAdminOut.model_validate(updated)


async def delete_destination(db: AsyncSession, destination_id: int) -> None:
    destination = await content_repository.admin_get_destination(db, destination_id)
    if not destination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination not found")
    await content_repository.admin_delete_destination(db, destination)


# ── Deals ──

async def list_deals(db: AsyncSession) -> list[DealAdminOut]:
    deals = await content_repository.admin_list_deals(db)
    return [DealAdminOut.model_validate(d) for d in deals]


async def create_deal(db: AsyncSession, payload: DealCreate) -> DealAdminOut:
    deal = await content_repository.admin_create_deal(db, **payload.model_dump())
    return DealAdminOut.model_validate(deal)


async def update_deal(db: AsyncSession, deal_id: int, payload: DealUpdate) -> DealAdminOut:
    deal = await content_repository.admin_get_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    updated = await content_repository.admin_update_deal(db, deal, **payload.model_dump())
    return DealAdminOut.model_validate(updated)


async def delete_deal(db: AsyncSession, deal_id: int) -> None:
    deal = await content_repository.admin_get_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    await content_repository.admin_delete_deal(db, deal)