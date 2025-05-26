from datetime import timedelta

from app.core.redis import get_alert_suppress_time, get_data_by_prefix, redis_client
from app.models.earthquake import EarthquakeAlert, EarthquakeData, EarthquakeEvent
from app.models.enums import AlertStatus, Location, SeverityLevel, TriState
from app.services.metrics import (
    observe_earthquake_alert_report,
    observe_earthquake_alert_suppress,
    observe_earthquake_alerts,
    observe_earthquake_alerts_autoclose,
    observe_earthquake_data,
    observe_earthquake_events,
)


def generate_events(data: EarthquakeData) -> list[EarthquakeEvent]:
    events = []
    magnitude = data.magnitude_value
    county_intensity_map = {
        area.county_name: area.area_intensity for area in data.shaking_area
    }

    for location in Location:
        # get intensity value for the location
        intensity = county_intensity_map.get(location, 0) if data.shaking_area else 0

        # determine severity level based on intensity and magnitude
        severity = classify_severity(magnitude, intensity)

        event = EarthquakeEvent(
            id=f"{data.id}-{location.value}",
            source=data.source,
            origin_time=data.origin_time,
            location=location,
            severity_level=severity,
        )
        events.append(event)

    return events


async def generate_alerts(events: list[EarthquakeEvent]) -> list[EarthquakeAlert]:
    alerts = []
    alert_suppress_time = await get_alert_suppress_time()

    for event in events:
        redis_key = f"alert_{event.source}_{event.location.value}"
        cached_alerts = await get_data_by_prefix(redis_key, EarthquakeAlert)
        cached_alert = max(cached_alerts, key=lambda a: a.origin_time, default=None)

        # found an existing alert with the same location as current event
        if cached_alert:
            cached_severity_level = cached_alert.severity_level
            cached_origin_time = cached_alert.origin_time

            # current event should be suppressed
            if (
                event.severity_level.value <= cached_severity_level
                and event.origin_time - cached_origin_time
                <= timedelta(
                    seconds=alert_suppress_time,
                )
            ):
                observe_earthquake_alert_suppress(event)
                continue

        # current event should trigger an alert
        if event.severity_level != SeverityLevel.NA:
            alert = EarthquakeAlert(
                **event.model_dump(),
                status=AlertStatus.OPEN,
                has_damage=TriState.UNKNOWN,
                needs_command_center=TriState.UNKNOWN,
                processing_duration=0,  # Add real logic later
            )
            alerts.append(alert)
            await redis_client.set(f"{redis_key}_{event.id}", alert.model_dump_json())

    return alerts


def classify_severity(magnitude: float, intensity: float) -> SeverityLevel:
    if magnitude >= 5 or intensity >= 3:
        return SeverityLevel.L2
    if intensity >= 1:
        return SeverityLevel.L1
    return SeverityLevel.NA


async def process_earthquake_data(data: EarthquakeData) -> list[EarthquakeAlert]:
    # update metrics for earthquake data
    observe_earthquake_data(data)

    events = generate_events(data)
    observe_earthquake_events(events)

    # obtain alerts by filtering events
    alerts = await generate_alerts(events)
    observe_earthquake_alerts(alerts)

    return alerts


def update_alert_metrics(alert: EarthquakeAlert) -> None:
    observe_earthquake_alert_report(alert)


def update_alert_autoclose_metrics(alert: EarthquakeAlert) -> None:
    observe_earthquake_alerts_autoclose(alert)
