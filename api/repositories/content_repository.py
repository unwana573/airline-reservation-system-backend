from sqlalchemy import func, or_, select
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


# ── Airports — public search (powers the Book page From/To fields) ──

async def search_airports(db: AsyncSession, query: str, limit: int = 10) -> list[Airport]:
    like_pattern = f"%{query}%"
    result = await db.execute(
        select(Airport)
        .where(
            or_(
                Airport.iata_code.ilike(like_pattern),
                Airport.city.ilike(like_pattern),
                Airport.name.ilike(like_pattern),
            )
        )
        .order_by(Airport.city)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_airport_by_iata(db: AsyncSession, iata_code: str) -> Airport | None:
    result = await db.execute(select(Airport).where(Airport.iata_code == iata_code))
    return result.scalar_one_or_none()


# ── Admin: airports ──

async def admin_list_airports(db: AsyncSession) -> list[Airport]:
    result = await db.execute(select(Airport).order_by(Airport.city))
    return list(result.scalars().all())


async def admin_create_airport(db: AsyncSession, iata_code: str, name: str, city: str, country: str) -> Airport:
    airport = Airport(iata_code=iata_code, name=name, city=city, country=country)
    db.add(airport)
    await db.commit()
    await db.refresh(airport)
    return airport


# ── Admin: featured destinations ──

async def admin_list_destinations(db: AsyncSession) -> list[FeaturedDestination]:
    result = await db.execute(select(FeaturedDestination).order_by(FeaturedDestination.display_order))
    return list(result.scalars().all())


async def admin_get_destination(db: AsyncSession, destination_id: int) -> FeaturedDestination | None:
    result = await db.execute(select(FeaturedDestination).where(FeaturedDestination.id == destination_id))
    return result.scalar_one_or_none()


async def admin_create_destination(db: AsyncSession, **fields) -> FeaturedDestination:
    destination = FeaturedDestination(**fields)
    db.add(destination)
    await db.commit()
    await db.refresh(destination)
    return destination


async def admin_update_destination(db: AsyncSession, destination: FeaturedDestination, **fields) -> FeaturedDestination:
    for key, value in fields.items():
        if value is not None:
            setattr(destination, key, value)
    await db.commit()
    await db.refresh(destination)
    return destination


async def admin_delete_destination(db: AsyncSession, destination: FeaturedDestination) -> None:
    await db.delete(destination)
    await db.commit()


# ── Admin: deals ──

async def admin_list_deals(db: AsyncSession) -> list[Deal]:
    result = await db.execute(select(Deal).order_by(Deal.display_order))
    return list(result.scalars().all())


async def admin_get_deal(db: AsyncSession, deal_id: int) -> Deal | None:
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    return result.scalar_one_or_none()


async def admin_create_deal(db: AsyncSession, **fields) -> Deal:
    deal = Deal(**fields)
    db.add(deal)
    await db.commit()
    await db.refresh(deal)
    return deal


async def admin_update_deal(db: AsyncSession, deal: Deal, **fields) -> Deal:
    for key, value in fields.items():
        if value is not None:
            setattr(deal, key, value)
    await db.commit()
    await db.refresh(deal)
    return deal


async def admin_delete_deal(db: AsyncSession, deal: Deal) -> None:
    await db.delete(deal)
    await db.commit()