import uuid
from typing import Any, Optional

from pydantic import BaseModel


class PaymentIntentRequest(BaseModel):
    pnr: str
    provider: str  # paystack|flutterwave


class PaymentIntentResponse(BaseModel):
    payment_id: uuid.UUID
    provider: str
    provider_reference: str
    authorization_url: str  # where the frontend redirects the user to pay
    amount: float
    currency: str


class PaymentOut(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    provider: str
    provider_reference: str
    amount: float
    currency: str
    status: str

    model_config = {"from_attributes": True}