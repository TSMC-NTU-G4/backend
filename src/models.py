from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ShakingArea(CustomBaseModel):
    county_name: str
    area_intensity: str


class EarthquakeData(CustomBaseModel):
    source: str
    origin_time: datetime
    epicenter_location: str
    magnitude_value: str
    focal_depth: str
    shaking_area: list[ShakingArea] | None = None
