from fastapi import APIRouter

from app.models.earthquake import EarthquakeAlert, EarthquakeData
from app.services.earthquake import generate_alerts, generate_events
from app.services.metrics import (
    observe_earthquake_alerts,
    observe_earthquake_data,
    observe_earthquake_events,
)

router = APIRouter(prefix="/api/earthquake", tags=["earthquake"])


@router.post("/")
def create_earthquake(data: EarthquakeData) -> list[EarthquakeAlert]:
    # update metrics for earthquake data
    observe_earthquake_data(data)

    # obtain alerts by filtering events
    events = generate_events(data)
    observe_earthquake_events(events)
    alerts = generate_alerts(events)
    observe_earthquake_alerts(alerts)
    return alerts
