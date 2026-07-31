import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    passengers: int
    cabin_class: Optional[str] = "economy"


class FlightSearchResult(BaseModel):
    flight_instance_id: uuid.UUID
    flight_number: str
    airline_name: str
    departure_at: datetime
    arrival_at: datetime
    duration_minutes: int
    price: float
    seats_available: int


class FlightDetailOut(BaseModel):
    flight_instance_id: uuid.UUID
    flight_number: str
    airline_name: str
    origin_code: str
    destination_code: str
    departure_at: datetime
    arrival_at: datetime
    status: str