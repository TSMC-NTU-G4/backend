from app.models.earthquake import EarthquakeData, EarthquakeEvent
from app.models.enums import Location, SeverityLevel


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
            source=data.source,
            origin_time=data.origin_time,
            location=location,
            severity_level=severity,
        )
        events.append(event)

    return events


def classify_severity(magnitude: float, intensity: float) -> SeverityLevel:
    if magnitude >= 5 or intensity >= 3:
        return SeverityLevel.L2
    if intensity >= 1:
        return SeverityLevel.L1
    return SeverityLevel.NA
