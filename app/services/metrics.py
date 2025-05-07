import uuid

from prometheus_client import Counter, Gauge

from app.models.earthquake import EarthquakeData

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


def observe_earthquake_data(data: EarthquakeData) -> None:
    # generate unique id
    earthquake_id = str(uuid.uuid4())

    # increment occurrence counter
    earthquake_occurrences_total.labels(source=data.source).inc()

    # set magnitude and depth value
    earthquake_magnitude.labels(
        id=earthquake_id,
        source=data.source,
        epicenter=data.epicenter_location,
    ).set(data.magnitude_value)
    earthquake_depth.labels(
        id=earthquake_id,
        source=data.source,
        epicenter=data.epicenter_location,
    ).set(data.focal_depth)
