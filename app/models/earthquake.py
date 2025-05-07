from datetime import datetime

from pydantic import BaseModel, Field

from .base import CustomBaseModel
from .enums import Location, SeverityLevel


class ShakingArea(CustomBaseModel):
    county_name: Location
    area_intensity: float


class EarthquakeData(CustomBaseModel):
    source: str
    origin_time: datetime
    epicenter_location: str
    magnitude_value: float
    focal_depth: float
    shaking_area: list[ShakingArea] = Field(default_factory=list)


class EarthquakeEvent(BaseModel):
    source: str
    origin_time: datetime
    location: Location
    severity_level: SeverityLevel
