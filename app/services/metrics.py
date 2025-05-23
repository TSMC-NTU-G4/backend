from prometheus_client import Counter, Gauge

from app.models.earthquake import EarthquakeAlert, EarthquakeData, EarthquakeEvent

# --- Earthquake data metrics ---
earthquake_occurrences_total = Counter(
    "earthquake_occurrences_total",
    "Total number of earthquake data",
    ["source"],
)
earthquake_magnitude = Gauge(
    "earthquake_magnitude",
    "Magnitude value of earthquake data",
    ["source", "id", "epicenter"],
)
earthquake_depth = Gauge(
    "earthquake_depth",
    "Focal depth of earthquake data",
    ["source", "id", "epicenter"],
)
earthquake_intensity = Gauge(
    "earthquake_intensity",
    "Area intensity of earthquake data",
    ["source", "id", "area"],
)


def observe_earthquake_data(data: EarthquakeData) -> None:
    # increment occurrence counter
    earthquake_occurrences_total.labels(source=data.source).inc()

    # set magnitude and depth value
    earthquake_magnitude.labels(
        id=str(data.id),
        source=data.source,
        epicenter=data.epicenter_location,
    ).set(data.magnitude_value)
    earthquake_depth.labels(
        id=str(data.id),
        source=data.source,
        epicenter=data.epicenter_location,
    ).set(data.focal_depth)

    # set intensity for each area
    for area in data.shaking_area:
        earthquake_intensity.labels(
            id=str(data.id),
            source=data.source,
            area=area.county_name.value,
        ).set(area.area_intensity)


# --- Earthquake event metrics ---
earthquake_events_total = Counter(
    "earthquake_events_total",
    "Total number of earthquake events",
    ["source"],
)
earthquake_events_severity = Gauge(
    "earthquake_events_severity",
    "Severity level of earthquake events",
    ["source", "id", "location"],
)


def observe_earthquake_events(events: list[EarthquakeEvent]) -> None:
    for event in events:
        earthquake_events_total.labels(source=event.source).inc()

        earthquake_events_severity.labels(
            id=str(event.id),
            source=event.source,
            location=event.location.value,
        ).set(event.severity_level.value)


# --- Earthquake alert metrics ---
earthquake_alerts_total = Counter(
    "earthquake_alerts_total",
    "Total number of earthquake alerts",
    ["source"],
)
earthquake_alerts_processed_total = Counter(
    "earthquake_alerts_processed_total",
    "Total number of processed earthquake alerts",
    ["source"],
)
earthquake_alerts_autoclosed_total = Counter(
    "earthquake_alerts_autoclosed_total",
    "Total number of autoclosed earthquake alerts",
    ["source"],
)
earthquake_alerts_damage = Gauge(
    "earthquake_alerts_damage",
    "Flag of whether there is damage in earthquake alerts",
    ["source", "id", "location", "origin_time"],
)
earthquake_alerts_command_center = Gauge(
    "earthquake_alerts_command_center",
    "Flag of whether command center is needed in earthquake alerts",
    ["source", "id", "location", "origin_time"],
)
earthquake_alerts_processing_duration = Gauge(
    "earthquake_alerts_processing_duration",
    "Processing duration of earthquake alerts",
    ["source", "id", "location", "origin_time"],
)


def observe_earthquake_alerts(alerts: list[EarthquakeAlert]) -> None:
    for alert in alerts:
        earthquake_alerts_total.labels(source=alert.source).inc()

        earthquake_alerts_damage.labels(
            id=str(alert.id),
            source=alert.source,
            location=alert.location.value,
            origin_time=alert.origin_time.isoformat(),
        ).set(alert.has_damage.value)

        earthquake_alerts_command_center.labels(
            id=str(alert.id),
            source=alert.source,
            location=alert.location.value,
            origin_time=alert.origin_time.isoformat(),
        ).set(alert.needs_command_center.value)

        earthquake_alerts_processing_duration.labels(
            id=str(alert.id),
            source=alert.source,
            location=alert.location.value,
            origin_time=alert.origin_time.isoformat(),
        ).set(alert.processing_duration)


def observe_earthquake_alert_report(alert: EarthquakeAlert) -> None:
    earthquake_alerts_processed_total.labels(source=alert.source).inc()

    earthquake_alerts_damage.labels(
        id=str(alert.id),
        source=alert.source,
        location=alert.location.value,
        origin_time=alert.origin_time.isoformat(),
    ).set(alert.has_damage.value)

    earthquake_alerts_command_center.labels(
        id=str(alert.id),
        source=alert.source,
        location=alert.location.value,
        origin_time=alert.origin_time.isoformat(),
    ).set(alert.needs_command_center.value)

    earthquake_alerts_processing_duration.labels(
        id=str(alert.id),
        source=alert.source,
        location=alert.location.value,
        origin_time=alert.origin_time.isoformat(),
    ).set(alert.processing_duration.total_seconds())


def observe_earthquake_alerts_autoclose(alert: EarthquakeAlert) -> None:
    earthquake_alerts_autoclosed_total.labels(source=alert.source).inc()
