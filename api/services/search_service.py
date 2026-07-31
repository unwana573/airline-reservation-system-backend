from datetime import date as date_type

from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories import flight_repository
from api.schemas.flights import FlightSearchResult


async def search_flights(
    db: AsyncSession,
    origin: str,
    destination: str,
    departure_date: date_type,
) -> list[FlightSearchResult]:
    rows = await flight_repository.search_flights(db, origin, destination, departure_date)

    results = []
    for flight_instance, schedule, airline, origin_airport, dest_airport, fare, fare_class in rows:
        duration_minutes = int((flight_instance.arrival_at - flight_instance.departure_at).total_seconds() // 60)

        results.append(
            FlightSearchResult(
                flight_instance_id=flight_instance.id,
                flight_number=schedule.flight_number,
                airline_name=airline.name,
                origin_code=origin_airport.iata_code,
                destination_code=dest_airport.iata_code,
                departure_at=flight_instance.departure_at,
                arrival_at=flight_instance.arrival_at,
                duration_minutes=duration_minutes,
                cabin_class=fare_class.name,
                price=fare.base_price,
                currency=fare.currency,
                seats_available=fare.seats_available,
            )
        )

    # Business rule: cheapest first. This is a service-layer decision
    # (what order to present results in), not a database concern —
    # keep it here rather than baking ORDER BY into the repository,
    # so future sort options (fastest, earliest) stay easy to add.
    results.sort(key=lambda r: r.price)

    return results