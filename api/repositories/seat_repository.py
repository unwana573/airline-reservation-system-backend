from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.models import Seat

async def get_seats_for_flight(db: AsyncSession, flight_instance_id: uuid.UUID) -> list[Seat]:
    result = await db.execute(
        select(Seat).where(Seat.flight_instance_id == flight_instance_id).order_by(Seat.seat_number)
    )
    return list(result.scalars().all())


async def get_seat_for_update(db: AsyncSession, seat_id: uuid.UUID) -> Seat | None:
    """Locks the seat row until the current transaction commits/rolls back.

    On Postgres this is a real row-level lock (SELECT ... FOR UPDATE) — a
    second concurrent request for the same seat blocks here until the first
    transaction finishes, then re-reads the now-updated status. This is what
    prevents two people from both successfully holding the same seat.
    SQLite (used for local dev/tests) doesn't support row-level locking the
    same way; it falls back to whole-database locking, which is weaker but
    fine for local testing since Postgres is what production actually runs.
    """
    result = await db.execute(
        select(Seat).where(Seat.id == seat_id).with_for_update()
    )
    return result.scalar_one_or_none()


async def mark_seat_held(db: AsyncSession, seat: Seat, held_until: datetime) -> Seat:
    seat.status = "held"
    seat.held_until = held_until
    await db.commit()
    await db.refresh(seat)
    return seat


async def release_seat(db: AsyncSession, seat: Seat) -> Seat:
    seat.status = "available"
    seat.held_until = None
    await db.commit()
    await db.refresh(seat)
    return seat


async def release_expired_holds(db: AsyncSession) -> int:
    """Finds every seat whose hold has expired and releases it back to
    available. Intended to run on a schedule (Celery beat) — see Phase 6."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Seat).where(Seat.status == "held", Seat.held_until < now)
    )
    expired_seats = result.scalars().all()
    for seat in expired_seats:
        seat.status = "available"
        seat.held_until = None
    await db.commit()
    return len(expired_seats)