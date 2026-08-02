import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Payment


async def get_payment_by_reference(db: AsyncSession, provider_reference: str) -> Payment | None:
    result = await db.execute(select(Payment).where(Payment.provider_reference == provider_reference))
    return result.scalar_one_or_none()


async def create_payment(
    db: AsyncSession,
    booking_id: uuid.UUID,
    provider: str,
    provider_reference: str,
    amount: float,
    currency: str,
) -> Payment:
    payment = Payment(
        booking_id=booking_id,
        provider=provider,
        provider_reference=provider_reference,
        amount=amount,
        currency=currency,
        status="pending",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def mark_payment_status(db: AsyncSession, payment: Payment, status: str) -> Payment:
    payment.status = status
    await db.commit()
    await db.refresh(payment)
    return payment