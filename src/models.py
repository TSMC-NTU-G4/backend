from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class CountyName(str, Enum):
    TAIPEI = "Taipei"
    HSINCHU = "Hsinchu"
    TAICHUNG = "Taichung"
    TAINAN = "Tainan"


class ShakingArea(CustomBaseModel):
    county_name: CountyName
    area_intensity: str


class EarthquakeData(CustomBaseModel):
    source: str
    origin_time: datetime
    epicenter_location: str
    magnitude_value: str
    focal_depth: str
    shaking_area: list[ShakingArea] | None = None


class SeverityLevel(str, Enum):
    NA = "NA"
    L1 = "L1"
    L2 = "L2"


class EarthquakeEvent(BaseModel):
    source: str
    origin_time: datetime
    county_name: CountyName
    severity_level: SeverityLevel
