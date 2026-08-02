import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.schemas.flights import FlightDetailOut, FlightSearchRequest, RoundTripSearchResponse
from api.services import search_service

router = APIRouter(tags=["flights"])


@router.post("/search/flights", response_model=RoundTripSearchResponse)
async def search_flights(payload: FlightSearchRequest, db: AsyncSession = Depends(get_db)):
    return await search_service.search_flights(db, payload)


@router.get("/flights/{flight_instance_id}", response_model=FlightDetailOut)
async def get_flight(flight_instance_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await search_service.get_flight_detail(db, flight_instance_id)   