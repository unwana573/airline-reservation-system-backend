import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models import Booking, BookingPassenger, BookingSegment


async def get_booking_by_pnr(db: AsyncSession, pnr: str) -> Booking | None:
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.segments), selectinload(Booking.passengers))
        .where(Booking.pnr == pnr)
    )
    return result.scalar_one_or_none()


async def pnr_exists(db: AsyncSession, pnr: str) -> bool:
    result = await db.execute(select(Booking.id).where(Booking.pnr == pnr))
    return result.scalar_one_or_none() is not None


async def create_booking(
    db: AsyncSession,
    pnr: str,
    trip_type: str,
    total_amount: float,
    currency: str,
    expires_at,
    guest_email: str | None = None,
    guest_phone: str | None = None,
    user_id: uuid.UUID | None = None,
) -> Booking:
    booking = Booking(
        pnr=pnr,
        trip_type=trip_type,
        total_amount=total_amount,
        currency=currency,
        expires_at=expires_at,
        guest_email=guest_email,
        guest_phone=guest_phone,
        user_id=user_id,
    )
    db.add(booking)
    await db.flush()  # get booking.id without committing yet — segments/passengers need it
    return booking


async def add_segment(db: AsyncSession, booking_id: uuid.UUID, flight_instance_id, fare_class_id: int, sequence: int) -> BookingSegment:
    segment = BookingSegment(
        booking_id=booking_id,
        flight_instance_id=flight_instance_id,
        fare_class_id=fare_class_id,
        sequence=sequence,
    )
    db.add(segment)
    await db.flush()
    return segment


async def get_booking_by_id(db: AsyncSession, booking_id: uuid.UUID) -> Booking | None:
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    return result.scalar_one_or_none()


async def update_booking_status(db: AsyncSession, booking: Booking, status: str) -> Booking:
    booking.status = status
    await db.commit()
    await db.refresh(booking)
    return booking


async def add_passenger(db: AsyncSession, booking_id: uuid.UUID, passenger_data: dict) -> BookingPassenger:
    passenger = BookingPassenger(booking_id=booking_id, **passenger_data)
    db.add(passenger)
    await db.flush()
    return passenger