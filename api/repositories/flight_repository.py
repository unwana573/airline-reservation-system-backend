# api/repositories/flight_repository.py

from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Airport, Airline, FlightInstance, FlightSchedule, Route, FareClass, FlightFare


async def search_flights(
    db: AsyncSession,
    origin_iata: str,
    destination_iata: str,
    departure_date: date_type,
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
        )
        .join(FlightSchedule, FlightInstance.schedule_id == FlightSchedule.id)
        .join(Airline, FlightSchedule.airline_id == Airline.id)
        .join(Route, FlightSchedule.route_id == Route.id)
        .join(OriginAirport, Route.origin_airport_id == OriginAirport.id)
        .join(DestinationAirport, Route.destination_airport_id == DestinationAirport.id)
        .join(FlightFare, FlightFare.flight_instance_id == FlightInstance.id)
        .join(FareClass, FlightFare.fare_class_id == FareClass.id)
        .where(
            OriginAirport.iata_code == origin_iata,
            DestinationAirport.iata_code == destination_iata,
            FlightInstance.flight_date == departure_date,
            FlightFare.seats_available > 0,
        )
    )

    result = await db.execute(stmt)
    return result.all()


async def get_flight_by_id(db: AsyncSession, flight_instance_id):
    result = await db.execute(
        select(FlightInstance).where(FlightInstance.id == flight_instance_id)
    )
    return result.scalar_one_or_none()