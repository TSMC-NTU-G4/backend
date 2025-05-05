from fastapi import APIRouter, Response, status

from models.earthquake import EarthquakeData
from services.earthquake import generate_events

router = APIRouter()


@router.post("/earthquake")
def create_earthquake(data: EarthquakeData) -> Response:
    a = generate_events(data)
    print(a)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
