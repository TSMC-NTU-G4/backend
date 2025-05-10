from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from .base import CustomBaseModel
from .enums import AlertStatus, Location, SeverityLevel, TriState


class ShakingArea(CustomBaseModel):
    county_name: Location
    area_intensity: float


class EarthquakeData(CustomBaseModel):
    id: UUID = Field(default_factory=uuid4)
    source: str
    origin_time: datetime
    epicenter_location: str
    magnitude_value: float
    focal_depth: float
    shaking_area: list[ShakingArea] = Field(default_factory=list)


class EarthquakeEvent(CustomBaseModel):
    id: str
    source: str
    origin_time: datetime
    location: Location
    severity_level: SeverityLevel


class EarthquakeAlert(EarthquakeEvent):
    status: AlertStatus
    has_damage: TriState
    needs_command_center: TriState
    processing_duration: int
