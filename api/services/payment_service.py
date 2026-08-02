import uuid

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.repositories import booking_repository, payment_repository
from api.schemas.payment import PaymentIntentRequest, PaymentIntentResponse

settings = get_settings()


async def create_payment_intent(db: AsyncSession, payload: PaymentIntentRequest) -> PaymentIntentResponse:
    booking = await booking_repository.get_booking_by_pnr(db, payload.pnr)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Booking is '{booking.status}', not payable",
        )

    if payload.provider == "paystack":
        provider_reference, authorization_url = await _init_paystack(booking)
    elif payload.provider == "flutterwave":
        provider_reference, authorization_url = await _init_flutterwave(booking)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported payment provider")

    payment = await payment_repository.create_payment(
        db,
        booking_id=booking.id,
        provider=payload.provider,
        provider_reference=provider_reference,
        amount=float(booking.total_amount),
        currency=booking.currency,
    )

    return PaymentIntentResponse(
        payment_id=payment.id,
        provider=payment.provider,
        provider_reference=payment.provider_reference,
        authorization_url=authorization_url,
        amount=float(payment.amount),
        currency=payment.currency,
    )


async def _init_paystack(booking) -> tuple[str, str]:
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Paystack is not configured")

    # Paystack expects the amount in kobo (smallest currency unit) for NGN.
    amount_kobo = int(float(booking.total_amount) * 100)
    reference = f"skyra_{booking.pnr}_{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.paystack.co/transaction/initialize",
            headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
            json={
                "email": booking.guest_email,
                "amount": amount_kobo,
                "reference": reference,
                "currency": booking.currency,
            },
        )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to initialize Paystack payment")

    data = response.json()["data"]
    return reference, data["authorization_url"]


async def _init_flutterwave(booking) -> tuple[str, str]:
    if not settings.flutterwave_secret_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Flutterwave is not configured")

    reference = f"skyra_{booking.pnr}_{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.flutterwave.com/v3/payments",
            headers={"Authorization": f"Bearer {settings.flutterwave_secret_key}"},
            json={
                "tx_ref": reference,
                "amount": str(booking.total_amount),
                "currency": booking.currency,
                "customer": {"email": booking.guest_email},
            },
        )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to initialize Flutterwave payment")

    data = response.json()["data"]
    return reference, data["link"]