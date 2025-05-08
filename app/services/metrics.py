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
