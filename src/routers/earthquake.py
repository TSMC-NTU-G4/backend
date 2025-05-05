from fastapi import APIRouter, Response, status

from models.earthquake import EarthquakeData
from services.earthquake import generate_events

router = APIRouter()


@router.post("/earthquake")
def create_earthquake(data: EarthquakeData) -> Response:
    generate_events(data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
