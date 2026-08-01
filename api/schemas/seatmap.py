import uuid
from datetime import datetime

from pydantic import BaseModel


class SeatOut(BaseModel):
    id: uuid.UUID
    seat_number: str
    cabin_class: str
    is_window: bool
    is_aisle: bool
    is_extra_legroom: bool
    is_emergency_exit: bool
    extra_price: float
    status: str

    model_config = {"from_attributes": True}


class SeatMapResponse(BaseModel):
    flight_instance_id: uuid.UUID
    seats_by_cabin: dict[str, list[SeatOut]]


class SeatHoldResponse(BaseModel):
    seat_id: uuid.UUID
    status: str
    held_until: datetime