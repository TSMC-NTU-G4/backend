import json
from datetime import datetime, timedelta

from app.core.redis import get_alert_suppress_time, redis_client
from app.models.earthquake import EarthquakeAlert, EarthquakeData, EarthquakeEvent
from app.models.enums import Location, SeverityLevel, TriState
from app.services.metrics import (
    observe_earthquake_alerts,
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


def generate_alerts(events: list[EarthquakeEvent]) -> list[EarthquakeAlert]:
    alerts = []
    alert_suppress_time = get_alert_suppress_time()

    for event in events:
        redis_key = f"alert_{event.location.value}"
        cached_alert = redis_client.get(redis_key)

        # found an existing alert with the same location as current event
        if cached_alert:
            cached_alert_json = json.loads(cached_alert)
            cached_severity_level = cached_alert_json.get("severity_level")
            cached_origin_time = datetime.fromisoformat(
                cached_alert_json.get("origin_time"),
            )

            # current event should be suppressed
            if (
                event.severity_level.value <= cached_severity_level
                and event.origin_time - cached_origin_time
                <= timedelta(
                    seconds=alert_suppress_time,
                )
            ):
                continue

        # current event should trigger an alert
        if event.severity_level != SeverityLevel.NA:
            alert = EarthquakeAlert(
                id=f"{event.id}",
                source=event.source,
                origin_time=event.origin_time,
                location=event.location,
                severity_level=event.severity_level,
                has_damage=TriState.UNKNOWN,
                needs_command_center=TriState.UNKNOWN,
                processing_duration=0,  # Add real logic later
            )
            alerts.append(alert)
            redis_client.set(redis_key, alert.model_dump_json())

    return alerts


def classify_severity(magnitude: float, intensity: float) -> SeverityLevel:
    if magnitude >= 5 or intensity >= 3:
        return SeverityLevel.L2
    if intensity >= 1:
        return SeverityLevel.L1
    return SeverityLevel.NA


def process_earthquake_data(data: EarthquakeData) -> list[EarthquakeAlert]:
    # update metrics for earthquake data
    observe_earthquake_data(data)

    events = generate_events(data)
    observe_earthquake_events(events)

    # obtain alerts by filtering events
    alerts = generate_alerts(events)
    observe_earthquake_alerts(alerts)

    return alerts
