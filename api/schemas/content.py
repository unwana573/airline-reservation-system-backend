from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class TrendingDestinationOut(BaseModel):
    airport_iata_code: str
    city: str
    country: str
    badge: Optional[str] = None
    image_url: Optional[str] = None
    from_price: Optional[float] = None  # cheapest fare currently found to this destination, if any
    currency: str = "NGN"


class DealOut(BaseModel):
    id: int
    title: str
    subtitle: str
    badge: Optional[str] = None
    promo_code: Optional[str] = None

    model_config = {"from_attributes": True}


class AirlineOut(BaseModel):
    id: int
    iata_code: str
    name: str

    model_config = {"from_attributes": True}


class AirportSearchOut(BaseModel):
    id: int
    iata_code: str
    name: str
    city: str
    country: str

    model_config = {"from_attributes": True}


class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr


class NewsletterSubscribeResponse(BaseModel):
    message: str