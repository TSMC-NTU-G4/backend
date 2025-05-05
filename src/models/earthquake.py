from datetime import datetime

from pydantic import BaseModel

from .base import CustomBaseModel
from .enums import Location, SeverityLevel


class ShakingArea(CustomBaseModel):
    county_name: Location
    area_intensity: str


class EarthquakeData(CustomBaseModel):
    source: str
    origin_time: datetime
    epicenter_location: str
    magnitude_value: str
    focal_depth: str
    shaking_area: list[ShakingArea] | None = None


class EarthquakeEvent(BaseModel):
    source: str
    origin_time: datetime
    location: Location
    severity_level: SeverityLevel
