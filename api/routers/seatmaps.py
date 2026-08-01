import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.schemas.seatmap import SeatHoldResponse, SeatMapResponse
from api.services import seat_lock_service

router = APIRouter(tags=["seatmaps"])


@router.get("/flights/{flight_instance_id}/seatmap", response_model=SeatMapResponse)
async def get_seatmap(flight_instance_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await seat_lock_service.get_seat_map(db, flight_instance_id)


@router.post("/flights/{flight_instance_id}/seats/{seat_id}/hold", response_model=SeatHoldResponse)
async def hold_seat(
    flight_instance_id: uuid.UUID,
    seat_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await seat_lock_service.hold_seat(db, seat_id)


@router.delete("/flights/{flight_instance_id}/seats/{seat_id}/hold", status_code=204)
async def release_seat(
    flight_instance_id: uuid.UUID,
    seat_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await seat_lock_service.release_seat_hold(db, seat_id)