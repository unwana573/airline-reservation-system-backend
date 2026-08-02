from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.database import get_db
from api.schemas.payment import PaymentIntentRequest, PaymentIntentResponse
from api.services import payment_service, webhook_service


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/intent", response_model=PaymentIntentResponse)
async def create_payment_intent(payload: PaymentIntentRequest, db: AsyncSession = Depends(get_db)):
    return await payment_service.create_payment_intent(db, payload)


@router.post("/webhook/paystack", status_code=200)
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    # Signature verification needs the exact raw bytes as sent — parsing to
    # JSON first and re-serializing can change whitespace/key order enough
    # to make a valid signature fail to verify. Always read the raw body.
    raw_body = await request.body()
    await webhook_service.process_paystack_webhook(db, raw_body, x_paystack_signature)
    return {"status": "received"}


@router.post("/webhook/flutterwave", status_code=200)
async def flutterwave_webhook(
    request: Request,
    verif_hash: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()
    await webhook_service.process_flutterwave_webhook(db, raw_body, verif_hash)
    return {"status": "received"}