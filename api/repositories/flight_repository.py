from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import AircraftType, Airline, Airport, FareClass, FlightFare, FlightInstance, FlightSchedule, Route


async def search_flights(
    db: AsyncSession,
    origin_iata: str,
    destination_iata: str,
    departure_date: date_type,
    max_price: float | None = None,
    airline_iata_codes: list[str] | None = None,
):
    OriginAirport = aliased(Airport)
    DestinationAirport = aliased(Airport)

    stmt = (
        select(
            FlightInstance,
            FlightSchedule,
            Airline,
            OriginAirport,
            DestinationAirport,
            FlightFare,
            FareClass,
            AircraftType,
        )
        .join(FlightSchedule, FlightInstance.schedule_id == FlightSchedule.id)
        .join(Airline, FlightSchedule.airline_id == Airline.id)
        .join(Route, FlightSchedule.route_id == Route.id)
        .join(OriginAirport, Route.origin_airport_id == OriginAirport.id)
        .join(DestinationAirport, Route.destination_airport_id == DestinationAirport.id)
        .join(FlightFare, FlightFare.flight_instance_id == FlightInstance.id)
        .join(FareClass, FlightFare.fare_class_id == FareClass.id)
        .outerjoin(AircraftType, FlightSchedule.aircraft_type_id == AircraftType.id)
        .where(
            OriginAirport.iata_code == origin_iata,
            DestinationAirport.iata_code == destination_iata,
            FlightInstance.flight_date == departure_date,
            FlightFare.seats_available > 0,
        )
    )

    # Filters applied in SQL where possible — cheaper than fetching everything
    # and filtering in Python, and keeps the "no matches" case fast.
    if max_price is not None:
        stmt = stmt.where(FlightFare.base_price <= max_price)
    if airline_iata_codes:
        stmt = stmt.where(Airline.iata_code.in_(airline_iata_codes))

    result = await db.execute(stmt)
    return result.all()


async def get_flight_with_details(db: AsyncSession, flight_instance_id):
    """Returns a single joined row (FlightInstance, FlightSchedule, Airline,
    OriginAirport, DestinationAirport) or None — everything needed for
    FlightDetailOut without a second query."""
    OriginAirport = aliased(Airport)
    DestinationAirport = aliased(Airport)

    stmt = (
        select(FlightInstance, FlightSchedule, Airline, OriginAirport, DestinationAirport)
        .join(FlightSchedule, FlightInstance.schedule_id == FlightSchedule.id)
        .join(Airline, FlightSchedule.airline_id == Airline.id)
        .join(Route, FlightSchedule.route_id == Route.id)
        .join(OriginAirport, Route.origin_airport_id == OriginAirport.id)
        .join(DestinationAirport, Route.destination_airport_id == DestinationAirport.id)
        .where(FlightInstance.id == flight_instance_id)
    )
    result = await db.execute(stmt)
    return result.first()


async def get_fare(db: AsyncSession, flight_instance_id, fare_class_id: int) -> FlightFare | None:
    result = await db.execute(
        select(FlightFare).where(
            FlightFare.flight_instance_id == flight_instance_id,
            FlightFare.fare_class_id == fare_class_id,
        )
    )
    return result.scalar_one_or_none()