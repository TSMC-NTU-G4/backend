from .models import CountyName, EarthquakeData, EarthquakeEvent, SeverityLevel


def generate_events(data: EarthquakeData) -> list[EarthquakeEvent]:
    events = []
    magnitude = float(data.magnitude_value)
    county_intensity_map = {
        area.county_name: float(area.area_intensity)
        for area in (data.shaking_area or [])
    }

    for county in CountyName:
        # get intensity value for the county
        intensity = county_intensity_map.get(county, 0) if data.shaking_area else 0

        # determine severity level based on intensity and magnitude
        severity = classify_severity(magnitude, intensity)

        event = EarthquakeEvent(
            source=data.source,
            origin_time=data.origin_time,
            county_name=county,
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
