import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories import seat_repository
from api.schemas.seatmap import SeatHoldResponse, SeatMapResponse, SeatOut

HOLD_DURATION_MINUTES = 10


async def get_seat_map(db: AsyncSession, flight_instance_id: uuid.UUID) -> SeatMapResponse:
    seats = await seat_repository.get_seats_for_flight(db, flight_instance_id)

    seats_by_cabin: dict[str, list[SeatOut]] = defaultdict(list)
    for seat in seats:
        seats_by_cabin[seat.cabin_class].append(SeatOut.model_validate(seat))

    return SeatMapResponse(flight_instance_id=flight_instance_id, seats_by_cabin=dict(seats_by_cabin))


async def hold_seat(db: AsyncSession, seat_id: uuid.UUID) -> SeatHoldResponse:
    # Locks the row for the duration of this transaction — a concurrent
    # request for the same seat_id blocks here (on Postgres) until this
    # transaction commits or rolls back, then sees the updated status.
    seat = await seat_repository.get_seat_for_update(db, seat_id)
    if not seat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")

    now = datetime.now(timezone.utc)

    # SQLite doesn't round-trip timezone info the way Postgres does, so a
    # value read back from the DB can come back naive even though it was
    # stored as UTC. Normalize before comparing so this works on both.
    held_until = seat.held_until
    if held_until is not None and held_until.tzinfo is None:
        held_until = held_until.replace(tzinfo=timezone.utc)

    hold_expired = seat.status == "held" and held_until is not None and held_until < now

    if seat.status == "occupied":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seat is already booked")

    if seat.status == "held" and not hold_expired:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seat is currently held by another passenger")

    new_held_until = now + timedelta(minutes=HOLD_DURATION_MINUTES)
    seat = await seat_repository.mark_seat_held(db, seat, new_held_until)

    return SeatHoldResponse(seat_id=seat.id, status=seat.status, held_until=seat.held_until)


async def release_seat_hold(db: AsyncSession, seat_id: uuid.UUID) -> None:
    seat = await seat_repository.get_seat_for_update(db, seat_id)
    if not seat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")

    if seat.status != "held":
        # Releasing a seat that isn't held is a no-op, not an error —
        # avoids punishing a client for a harmless double-release call.
        return

    await seat_repository.release_seat(db, seat)