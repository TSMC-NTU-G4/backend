from prometheus_client import Counter, Gauge

from app.models.earthquake import EarthquakeData

# --- Earthquake data metrics ---
earthquake_occurrences = Counter(
    "earthquake_occurrences",
    "Total number of earthquake data received",
    ["source"],
)
earthquake_magnitude = Gauge(
    "earthquake_magnitude",
    "Magnitude value of earthquake",
    ["source", "location"],
)


def observe_earthquake_data(data: EarthquakeData) -> None:
    earthquake_occurrences.labels(source=data.source).inc()
    earthquake_magnitude.labels(
        source=data.source,
        location=data.epicenter_location,
    ).set(data.magnitude_value)
