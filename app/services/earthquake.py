import json
from datetime import datetime, timedelta

from app.core.redis import redis_client
from app.models.earthquake import EarthquakeData, EarthquakeEvent
from app.models.enums import Location, SeverityLevel

# map severity level to their index
severity_level_dict = {level.value: i for i, level in enumerate(SeverityLevel)}


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


def generate_alerts(events: list[EarthquakeEvent]) -> list[EarthquakeEvent]:
    alerts = []

    for event in events:
        cached_alert = redis_client.get(f"alert_{event.location.value}")

        # found an existing alert with the same location as current event
        if cached_alert:
            cached_alert_json = json.loads(cached_alert)
            cached_severity_level = cached_alert_json.get("severity_level")
            cached_origin_time = datetime.fromisoformat(
                cached_alert_json.get("origin_time"),
            )

            # current event should be suppressed
            # TODO: replace harcoded 1min with ALERT_SUPPRESS_TIME env variable
            if severity_level_dict[event.severity_level.value] <= severity_level_dict[
                cached_severity_level
            ] and event.origin_time - cached_origin_time <= timedelta(minutes=1):
                continue

        # current event should trigger an alert
        if event.severity_level != SeverityLevel.NA:
            alerts.append(event)
            alert_json = event.model_dump_json()
            redis_client.set(f"alert_{event.location.value}", alert_json)

    return alerts


def classify_severity(magnitude: float, intensity: float) -> SeverityLevel:
    if magnitude >= 5 or intensity >= 3:
        return SeverityLevel.L2
    if intensity >= 1:
        return SeverityLevel.L1
    return SeverityLevel.NA
