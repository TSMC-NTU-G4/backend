from fastapi import APIRouter, HTTPException

from app.core.redis import get_data_by_prefix, redis_client
from app.models.earthquake import EarthquakeAlert, EarthquakeData
from app.models.enums import AlertStatus
from app.models.response import Response
from app.services.earthquake import process_earthquake_data, update_alert_metrics

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


@router.put("/alerts/{alert_id}")
def process_earthquake_alert(alert_id: str, alert: EarthquakeAlert) -> Response:
    # determine if processed alert is still in redis cache
    redis_key = f"alert_{alert.source}_{alert.location.value}_{alert_id}"
    cached_alert = redis_client.get(redis_key)
    if not cached_alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # update processing duration
    alert.processing_duration = alert.processed_time - alert.origin_time

    # update alert metrics
    update_alert_metrics(alert)

    # delete alert from redis
    redis_client.delete(redis_key)
    return {"message": f"Processed alert {alert_id} successfully"}
