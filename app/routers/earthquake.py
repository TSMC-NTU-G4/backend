from fastapi import APIRouter, Response, status

from app.models.earthquake import EarthquakeData
from app.services.earthquake import generate_events
from app.services.metrics import observe_earthquake_data

router = APIRouter()


@router.post("/earthquake")
def create_earthquake(data: EarthquakeData) -> Response:
    # update metrics for earthquake data
    observe_earthquake_data(data)

    generate_events(data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
