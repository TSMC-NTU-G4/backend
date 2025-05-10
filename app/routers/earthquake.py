from fastapi import APIRouter

from app.core.redis import get_data_by_prefix
from app.models.earthquake import EarthquakeAlert, EarthquakeData
from app.models.enums import AlertStatus
from app.models.response import Response
from app.services.earthquake import process_earthquake_data

router = APIRouter(prefix="/api/earthquake", tags=["earthquake"])


@router.post("/")
def create_earthquake(data: EarthquakeData) -> Response:
    process_earthquake_data(data)
    return {"message": f"Created earthquake {data.id} successfully"}


@router.get("/alerts")
def get_earthquake_alerts() -> Response[list[EarthquakeAlert]]:
    alerts = get_data_by_prefix("alert", EarthquakeAlert)
    alerts.sort(
        key=lambda alert: (
            -alert.origin_time.timestamp(),
            alert.location.value,
            alert.source,
        ),
    )

    # filter only alerts where status is OPEN
    open_alerts = [alert for alert in alerts if alert.status == AlertStatus.OPEN]
    return {"message": f"Found {len(open_alerts)} alerts data", "data": open_alerts}
