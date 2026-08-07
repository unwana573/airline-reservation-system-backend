from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.schemas.content import (
    AirlineOut,
    AirportSearchOut,
    DealOut,
    NewsletterSubscribeRequest,
    NewsletterSubscribeResponse,
    TrendingDestinationOut,
)
from api.services import content_service

router = APIRouter(tags=["content"])


@router.get("/destinations/trending", response_model=list[TrendingDestinationOut])
async def trending_destinations(db: AsyncSession = Depends(get_db)):
    return await content_service.get_trending_destinations(db)


@router.get("/deals", response_model=list[DealOut])
async def active_deals(db: AsyncSession = Depends(get_db)):
    return await content_service.get_active_deals(db)


@router.get("/airlines", response_model=list[AirlineOut])
async def airlines(db: AsyncSession = Depends(get_db)):
    return await content_service.get_airlines(db)


@router.get("/airports/search", response_model=list[AirportSearchOut])
async def search_airports(q: str, db: AsyncSession = Depends(get_db)):
    """Powers the From/To autocomplete on the Book page. Airports shown
    here are exactly the ones admins have added via POST /admin/airports."""
    return await content_service.search_airports(db, q)


@router.post("/newsletter/subscribe", response_model=NewsletterSubscribeResponse)
async def subscribe(payload: NewsletterSubscribeRequest, db: AsyncSession = Depends(get_db)):
    return await content_service.subscribe_to_newsletter(db, payload.email)