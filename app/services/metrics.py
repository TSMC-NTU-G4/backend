import uuid

from prometheus_client import Counter, Gauge

from app.models.earthquake import EarthquakeData

# --- Earthquake data metrics ---
earthquake_occurrences = Counter(
    "earthquake_occurrences",
    "Total number of earthquake data",
    ["source"],
)
earthquake_magnitude = Gauge(
    "earthquake_magnitude",
    "Magnitude value of earthquake data",
    ["source", "id", "location"],
)
earthquake_depth = Gauge(
    "earthquake_depth",
    "Focal depth of earthquake data",
    ["source", "id", "location"],
)


def observe_earthquake_data(data: EarthquakeData) -> None:
    # generate unique id
    earthquake_id = str(uuid.uuid4())

    # increment occurrence counter
    earthquake_occurrences.labels(source=data.source).inc()

    # set magnitude and depth value
    earthquake_magnitude.labels(
        id=earthquake_id,
        source=data.source,
        location=data.epicenter_location,
    ).set(data.magnitude_value)
    earthquake_depth.labels(
        id=earthquake_id,
        source=data.source,
        location=data.epicenter_location,
    ).set(data.focal_depth)
