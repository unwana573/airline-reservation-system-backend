import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator


class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date               # ISO format only: "2026-08-01"
    return_date: Optional[date] = None  # presence of this = round trip search
    passengers: int = 1
    cabin_class: Optional[str] = "economy"

    # Filters — all optional, apply only when provided
    max_price: Optional[float] = None
    max_stops: Optional[int] = None          # 0 = nonstop only, 1 = up to one stop, etc.
    airline_iata_codes: Optional[list[str]] = None

    # Sort
    sort_by: Literal["cheapest", "fastest", "earliest", "best"] = "cheapest"

    @field_validator("return_date")
    @classmethod
    def return_after_departure(cls, v: Optional[date], info) -> Optional[date]:
        departure = info.data.get("departure_date")
        if v is not None and departure is not None and v < departure:
            raise ValueError("return_date cannot be before departure_date")
        return v


class FlightSearchResult(BaseModel):
    flight_instance_id: uuid.UUID
    fare_class_id: int
    flight_number: str
    airline_name: str
    airline_iata_code: str
    aircraft_model: Optional[str] = None
    origin_code: str
    destination_code: str
    departure_at: datetime
    arrival_at: datetime
    duration_minutes: int
    stops: int = 0  # always 0 for now — no multi-segment itineraries yet, see note in service
    cabin_class: str
    refundable: bool
    baggage_allowance_kg: int
    price: float
    currency: str
    seats_available: int

    model_config = {"from_attributes": True}


class RoundTripSearchResponse(BaseModel):
    outbound: list[FlightSearchResult]
    inbound: list[FlightSearchResult] = []  # empty when this was a one-way search


class FlightDetailOut(BaseModel):
    flight_instance_id: uuid.UUID
    flight_number: str
    airline_name: str
    origin_code: str
    destination_code: str
    departure_at: datetime
    arrival_at: datetime
    status: str

    model_config = {"from_attributes": True}