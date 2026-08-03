from fastapi import APIRouter

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


@router.get("/")
async def get_bookings():
    return {
        "message": "Bookings endpoint"
    }