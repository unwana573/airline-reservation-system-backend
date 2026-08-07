from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AirportCreate(BaseModel):
    iata_code: str
    name: str
    city: str
    country: str


class AirportOut(BaseModel):
    id: int
    iata_code: str
    name: str
    city: str
    country: str

    model_config = {"from_attributes": True}


class FeaturedDestinationCreate(BaseModel):
    airport_iata_code: str  # looked up server-side, frontend never needs to know the internal airport_id
    badge: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    description: Optional[str] = None
    best_time_to_visit: Optional[str] = None
    popular_attractions: Optional[str] = None
    travel_requirements: Optional[str] = None


class FeaturedDestinationUpdate(BaseModel):
    badge: Optional[str] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    best_time_to_visit: Optional[str] = None
    popular_attractions: Optional[str] = None
    travel_requirements: Optional[str] = None


class FeaturedDestinationAdminOut(BaseModel):
    id: int
    airport_id: int
    badge: Optional[str]
    image_url: Optional[str]
    display_order: int
    is_active: bool
    description: Optional[str]
    best_time_to_visit: Optional[str]
    popular_attractions: Optional[str]
    travel_requirements: Optional[str]

    model_config = {"from_attributes": True}


class DealCreate(BaseModel):
    title: str
    subtitle: str
    badge: Optional[str] = None
    promo_code: Optional[str] = None
    is_active: bool = True
    display_order: int = 0
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class DealUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    badge: Optional[str] = None
    promo_code: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class DealAdminOut(BaseModel):
    id: int
    title: str
    subtitle: str
    badge: Optional[str]
    promo_code: Optional[str]
    is_active: bool
    display_order: int
    valid_from: Optional[datetime]
    valid_to: Optional[datetime]

    model_config = {"from_attributes": True}