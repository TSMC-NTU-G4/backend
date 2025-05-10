import json

from fastapi import APIRouter

from app.core.redis import redis_client
from app.models.earthquake import EarthquakeAlert, EarthquakeData
from app.models.response import Response
from app.services.earthquake import process_earthquake_data

router = APIRouter(prefix="/api/earthquake", tags=["earthquake"])


@router.post("/")
def create_earthquake(data: EarthquakeData) -> Response:
    process_earthquake_data(data)
    return {"message": f"Created earthquake {data.id} successfully"}


@router.get("/alerts")
def get_earthquake_alerts() -> Response[list[EarthquakeAlert]]:
    cursor = 0
    alerts = []

    # get all alerts data from redis cache
    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match="alert_*", count=100)
        for key in keys:
            alert_data = redis_client.get(key)
            if alert_data:
                try:
                    alerts.append(json.loads(alert_data))
                except json.JSONDecodeError:
                    continue
        if cursor == 0:
            break

    return {"message": f"Found {len(alerts)} alerts data", "data": alerts}
