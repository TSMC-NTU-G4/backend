from fastapi import APIRouter

from app.models.earthquake import EarthquakeAlert, EarthquakeData
from app.services.earthquake import generate_alerts, generate_events
from app.services.metrics import observe_earthquake_data

router = APIRouter(prefix="/api/earthquake", tags=["earthquake"])


@router.post("/")
def create_earthquake(data: EarthquakeData) -> list[EarthquakeAlert]:
    # update metrics for earthquake data
    observe_earthquake_data(data)

    # obtain alerts by filtering events
    events = generate_events(data)
    return generate_alerts(events)
