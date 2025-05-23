import json
from datetime import UTC, datetime, timedelta

import pytz
from fastapi import APIRouter, HTTPException

from app.core.redis import get_data_by_prefix, redis_client
from app.models.earthquake import EarthquakeAlert, EarthquakeData, ShakingArea
from app.models.enums import AlertStatus
from app.models.response import Response
from app.services.earthquake import (
    process_earthquake_data,
    update_alert_autoclose_metrics,
    update_alert_metrics,
)
from app.utils.logger import logger
from app.utils.realtime_data_handler import fetch_realtime_data

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

            # log autoclosed alert
            logger.info(
                f"Auto-closed alert ID {alert.id} from source {alert.source} at {alert.location.value}.",
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
        return {"message": "No realtime earthquake data available at the moment."}

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

    shaking_area_list = []
    earthquake_flag = False
    for area_data in area_statuses:
        area_name = area_data.get("name")

        if area_name is not None:
            intensity = float(area_data.get("intensity_float", 0.0))
            if intensity > 0:
                earthquake_flag = True
            shaking_area_list.append(
                ShakingArea(county_name=area_name, area_intensity=intensity),
            )

    if not earthquake_flag:
        return {"message": "No realtime earthquake data available at the moment."}

    # An earthquake is currently happening
    formatted_data = EarthquakeData(
        source="TREM-Lite",
        origin_time=origin_time_str,
        epicenter_location="",
        magnitude_value=0,
        focal_depth=0,
        shaking_area=shaking_area_list,
    )
    # Generate corresponding events and alerts
    alerts = await process_earthquake_data(formatted_data)

    for alert in alerts:
        # log realtime alert
        logger.info(
            f"Received realtime alert ID {alert.id} from source {alert.source} at {alert.location.value}.",
        )

        # Publish alert to redis channel
        await redis_client.publish(
            "alerts",
            json.dumps(
                {
                    "type": AlertStatus.OPEN,
                    "alert": alert.model_dump_json(by_alias=True),
                },
            ),
        )

    return {
        "message": "Realtime earthquake data fetched successfully",
        "data": formatted_data,
    }
