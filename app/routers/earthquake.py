import json
from datetime import datetime, timedelta

import pytz
from fastapi import APIRouter, HTTPException

from app.core.redis import get_data_by_prefix, redis_client
from app.models.earthquake import EarthquakeAlert, EarthquakeData
from app.models.enums import AlertStatus
from app.models.response import Response
from app.services.earthquake import (
    process_earthquake_data,
    update_alert_autoclose_metrics,
    update_alert_metrics,
)

router = APIRouter(prefix="/api/earthquake", tags=["earthquake"])


@router.post("/")
async def create_earthquake(data: EarthquakeData) -> Response:
    await process_earthquake_data(data)
    return {"message": f"Created earthquake {data.id} successfully"}


@router.get("/alerts")
async def get_earthquake_alerts() -> Response[list[EarthquakeAlert]]:
    alerts = await get_data_by_prefix("alert", EarthquakeAlert)
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
async def process_earthquake_alert(alert_id: str, alert: EarthquakeAlert) -> Response:
    # determine if processed alert is still in redis cache
    redis_key = f"alert_{alert.source}_{alert.location.value}_{alert_id}"
    cached_alert = await redis_client.get(redis_key)
    if not cached_alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # update processing duration
    alert.processing_duration = alert.processed_time - alert.origin_time

    # update alert metrics
    update_alert_metrics(alert)

    # delete alert from redis
    await redis_client.delete(redis_key)
    return {"message": f"Processed alert {alert_id} successfully"}


@router.delete("/alerts/autoclose")
async def autoclose_expired_alerts() -> Response:
    # fetch all alerts from redis
    alerts = await get_data_by_prefix("alert", EarthquakeAlert)
    taipei_tz = pytz.timezone("Asia/Taipei")
    now = datetime.now(taipei_tz)
    expired_count = 0

    for alert in alerts:
        # ensure alert origin time includes timezone info
        if alert.origin_time.tzinfo is None:
            alert.origin_time = taipei_tz.localize(alert.origin_time)

        # current alert is not responded within 1 hr
        if alert.status == AlertStatus.OPEN and (now - alert.origin_time) > timedelta(
            minutes=1,
        ):
            # set alert status as autoclosed
            alert.status = AlertStatus.AUTOCLOSED
            expired_count += 1

            # update alert metrics
            update_alert_autoclose_metrics(alert)

            # remove alert from redis
            await redis_client.delete(
                f"alert_{alert.source}_{alert.location.value}_{alert.id}",
            )

            # publish alert to redis channel
            await redis_client.publish(
                "alerts",
                json.dumps(
                    {"type": AlertStatus.AUTOCLOSED, "alert": alert.model_dump_json()},
                ),
            )

    return {"message": f"Auto-closed {expired_count} expired alerts."}
