from datetime import date as date_type

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories import flight_repository
from api.schemas.flights import FlightDetailOut, FlightSearchRequest, FlightSearchResult, RoundTripSearchResponse


def _row_to_result(row) -> FlightSearchResult:
    flight_instance, schedule, airline, origin_airport, dest_airport, fare, fare_class, aircraft_type = row
    duration_minutes = int((flight_instance.arrival_at - flight_instance.departure_at).total_seconds() // 60)

    return FlightSearchResult(
        flight_instance_id=flight_instance.id,
        fare_class_id=fare_class.id,
        flight_number=schedule.flight_number,
        airline_name=airline.name,
        airline_iata_code=airline.iata_code,
        aircraft_model=aircraft_type.model if aircraft_type else None,
        origin_code=origin_airport.iata_code,
        destination_code=dest_airport.iata_code,
        departure_at=flight_instance.departure_at,
        arrival_at=flight_instance.arrival_at,
        duration_minutes=duration_minutes,
        stops=0,  # no multi-segment itinerary model yet — see note below
        cabin_class=fare_class.name,
        refundable=fare_class.refundable,
        baggage_allowance_kg=fare_class.baggage_allowance_kg,
        price=float(fare.base_price),
        currency=fare.currency,
        seats_available=fare.seats_available,
    )


def _apply_sort(results: list[FlightSearchResult], sort_by: str) -> list[FlightSearchResult]:
    if sort_by == "cheapest":
        return sorted(results, key=lambda r: r.price)
    if sort_by == "fastest":
        return sorted(results, key=lambda r: r.duration_minutes)
    if sort_by == "earliest":
        return sorted(results, key=lambda r: r.departure_at)
    if sort_by == "best":
        # "Best" = a simple blended score favoring low price and short duration
        # roughly equally. This is a starting heuristic, not a final ranking
        # algorithm — worth revisiting once you have real booking data to see
        # what "best" should actually weight (on-time performance, reviews, etc).
        max_price = max((r.price for r in results), default=1) or 1
        max_duration = max((r.duration_minutes for r in results), default=1) or 1
        return sorted(results, key=lambda r: (r.price / max_price) + (r.duration_minutes / max_duration))
    return results


async def _search_one_leg(
    db: AsyncSession,
    origin: str,
    destination: str,
    flight_date: date_type,
    payload: FlightSearchRequest,
) -> list[FlightSearchResult]:
    rows = await flight_repository.search_flights(
        db,
        origin,
        destination,
        flight_date,
        max_price=payload.max_price,
        airline_iata_codes=payload.airline_iata_codes,
    )

    results = [_row_to_result(row) for row in rows]

    # max_stops has no effect yet — there is no multi-segment/connecting
    # itinerary concept in the current schema (every flight_instance is a
    # single nonstop leg). Accepted as a documented no-op rather than
    # silently ignored, so the API contract is honest about current scope.

    return _apply_sort(results, payload.sort_by)


async def search_flights(db: AsyncSession, payload: FlightSearchRequest) -> RoundTripSearchResponse:
    outbound = await _search_one_leg(db, payload.origin.upper(), payload.destination.upper(), payload.departure_date, payload)

    inbound: list[FlightSearchResult] = []
    if payload.return_date is not None:
        # Round trip: search the return leg with origin/destination swapped.
        inbound = await _search_one_leg(
            db, payload.destination.upper(), payload.origin.upper(), payload.return_date, payload
        )

    return RoundTripSearchResponse(outbound=outbound, inbound=inbound)


async def get_flight_detail(db: AsyncSession, flight_instance_id) -> FlightDetailOut:
    row = await flight_repository.get_flight_with_details(db, flight_instance_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")

    flight_instance, schedule, airline, origin_airport, dest_airport = row

    return FlightDetailOut(
        flight_instance_id=flight_instance.id,
        flight_number=schedule.flight_number,
        airline_name=airline.name,
        origin_code=origin_airport.iata_code,
        destination_code=dest_airport.iata_code,
        departure_at=flight_instance.departure_at,
        arrival_at=flight_instance.arrival_at,
        status=flight_instance.status,
    )