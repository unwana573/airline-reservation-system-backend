from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories import content_repository
from api.schemas.content import (
    AirlineOut,
    DealOut,
    NewsletterSubscribeResponse,
    TrendingDestinationOut,
)


async def get_trending_destinations(db: AsyncSession) -> list[TrendingDestinationOut]:
    rows = await content_repository.get_active_featured_destinations(db)

    results = []
    for featured, airport in rows:
        cheapest_fare = await content_repository.get_cheapest_fare_to_airport(db, airport.id)
        results.append(
            TrendingDestinationOut(
                airport_iata_code=airport.iata_code,
                city=airport.city,
                country=airport.country,
                badge=featured.badge,
                image_url=featured.image_url,
                from_price=float(cheapest_fare.base_price) if cheapest_fare else None,
                currency=cheapest_fare.currency if cheapest_fare else "NGN",
            )
        )
    return results


async def get_active_deals(db: AsyncSession) -> list[DealOut]:
    deals = await content_repository.get_active_deals(db)
    return [DealOut.model_validate(d) for d in deals]


async def get_airlines(db: AsyncSession) -> list[AirlineOut]:
    airlines = await content_repository.get_all_airlines(db)
    return [AirlineOut.model_validate(a) for a in airlines]


async def subscribe_to_newsletter(db: AsyncSession, email: str) -> NewsletterSubscribeResponse:
    if await content_repository.subscriber_exists(db, email):
        # Not an error — resubscribing with the same email should feel like
        # success to the user, not a confusing conflict.
        return NewsletterSubscribeResponse(message="You're already subscribed.")

    await content_repository.add_subscriber(db, email)
    return NewsletterSubscribeResponse(message="Subscribed — welcome aboard.")