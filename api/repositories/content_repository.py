from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Airline, Airport, Deal, FeaturedDestination, FlightFare, FlightInstance, FlightSchedule, NewsletterSubscriber, Route


async def get_active_featured_destinations(db: AsyncSession) -> list[tuple[FeaturedDestination, Airport]]:
    result = await db.execute(
        select(FeaturedDestination, Airport)
        .join(Airport, FeaturedDestination.airport_id == Airport.id)
        .where(FeaturedDestination.is_active.is_(True))
        .order_by(FeaturedDestination.display_order)
    )
    return result.all()


async def get_cheapest_fare_to_airport(db: AsyncSession, airport_id: int) -> FlightFare | None:
    """Cheapest currently-available fare on any route ending at this airport —
    used to populate the "from $X" price shown on destination cards."""
    result = await db.execute(
        select(FlightFare)
        .join(FlightInstance, FlightFare.flight_instance_id == FlightInstance.id)
        .join(FlightSchedule, FlightInstance.schedule_id == FlightSchedule.id)
        .join(Route, FlightSchedule.route_id == Route.id)
        .where(Route.destination_airport_id == airport_id, FlightFare.seats_available > 0)
        .order_by(FlightFare.base_price.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_active_deals(db: AsyncSession) -> list[Deal]:
    result = await db.execute(
        select(Deal).where(Deal.is_active.is_(True)).order_by(Deal.display_order)
    )
    return list(result.scalars().all())


async def get_all_airlines(db: AsyncSession) -> list[Airline]:
    result = await db.execute(select(Airline).order_by(Airline.name))
    return list(result.scalars().all())


async def subscriber_exists(db: AsyncSession, email: str) -> bool:
    result = await db.execute(select(NewsletterSubscriber.id).where(NewsletterSubscriber.email == email))
    return result.scalar_one_or_none() is not None


async def add_subscriber(db: AsyncSession, email: str) -> NewsletterSubscriber:
    subscriber = NewsletterSubscriber(email=email)
    db.add(subscriber)
    await db.commit()
    await db.refresh(subscriber)
    return subscriber