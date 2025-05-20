import json
import uuid
from datetime import UTC, datetime, timedelta

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
from app.utils.realtime_data_handler import fetch_realtime_data

router = APIRouter(prefix="/api/earthquake", tags=["earthquake"])

# This should ideally be imported from a central config or the module providing fetch_realtime_data
TARGET_AREAS_CONFIG_FOR_ROUTER = [
    {"code": 106, "name": "臺北市大安區"},
    {"code": 402, "name": "臺中市南區"},
    {"code": 710, "name": "臺南市永康區"},
    {"code": 301, "name": "新竹市東區"},
]
TARGET_AREAS_NAME_TO_CODE_MAP_FOR_ROUTER = {
    area["name"]: area["code"] for area in TARGET_AREAS_CONFIG_FOR_ROUTER
}


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
            hours=1,
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


@router.get("/realtime")
async def get_realtime_earthquake_data() -> Response:
    area_statuses = (
        await fetch_realtime_data()
    )  # This is the list of dicts from terminal log
    if not area_statuses:
        # Return a default structure or an appropriate message if no data
        return {
            "message": "No realtime earthquake data available at the moment.",
            "data": {
                "id": str(uuid.uuid4()),
                "source": "TREM-Lite",
                "origin_time": datetime.now(pytz.timezone("Asia/Taipei")).isoformat(),
                "epicenter_location": "Unknown",
                "magnitude_value": 0.0,
                "focal_depth": 0,
                "shaking_area": [],
            },
        }

    # Determine origin_time from the most recent lastUpdate, default to first area's update or now
    origin_datetime_obj = None
    latest_update_time = None

    for status_item in area_statuses:
        if status_item.get("lastUpdate"):
            current_item_update_time = status_item["lastUpdate"]
            if (
                latest_update_time is None
                or current_item_update_time > latest_update_time
            ):
                latest_update_time = current_item_update_time

    origin_datetime_obj = latest_update_time
    taipei_tz = pytz.timezone("Asia/Taipei")

    if origin_datetime_obj:
        # Ensure datetime is timezone-aware (assume UTC if naive, then convert to Taipei)
        if origin_datetime_obj.tzinfo is None:
            # If naive, assume it's UTC, then convert to Taipei
            origin_datetime_obj = origin_datetime_obj.replace(tzinfo=UTC).astimezone(
                taipei_tz,
            )
        else:
            # If already timezone-aware, just convert to Taipei
            origin_datetime_obj = origin_datetime_obj.astimezone(taipei_tz)
        origin_time_str = origin_datetime_obj.isoformat()
    else:
        # If no specific update time, use current time in Taipei timezone
        origin_time_str = datetime.now(taipei_tz).isoformat()

    # Determine magnitude_value (e.g., from the first area, assuming it's a unified value)
    magnitude_value = 0.0

    shaking_area_list = []
    for area_data in area_statuses:
        area_name = area_data.get("name")
        area_code = TARGET_AREAS_NAME_TO_CODE_MAP_FOR_ROUTER.get(area_name)

        if area_code is not None:
            intensity = float(area_data.get("intensity_float", 0.0))
            if intensity < 0:
                intensity = 0
            shaking_area_list.append(
                {
                    "county_name": {"name": area_name, "code": area_code},
                    "area_intensity": intensity,
                    "pga": area_data.get("pga", 0.0),
                },
            )

    formatted_data = {
        "id": str(uuid.uuid4()),
        "source": "TREM-Lite",
        "origin_time": origin_time_str,
        "epicenter_location": "Unknown",  # As per original JS and image
        "magnitude_value": magnitude_value,
        "focal_depth": 0,  # As per original JS and image
        "shaking_area": shaking_area_list,
    }

    return {
        "message": "Realtime earthquake data fetched successfully",
        "data": formatted_data,
    }
