from fastapi import APIRouter

from app.models.earthquake import EarthquakeData, EarthquakeEvent
from app.services.earthquake import generate_alerts, generate_events
from app.services.metrics import observe_earthquake_data

router = APIRouter()


@router.post("/earthquake")
def create_earthquake(data: EarthquakeData) -> list[EarthquakeEvent]:
    # update metrics for earthquake data
    observe_earthquake_data(data)

    # obtain alerts by filtering events
    events = generate_events(data)
    return generate_alerts(events)
