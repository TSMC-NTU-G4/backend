from datetime import datetime
from uuid import UUID

from app.models.earthquake import (
    EarthquakeAlert,
    EarthquakeData,
    EarthquakeEvent,
    ShakingArea,
)
from app.models.enums import AlertStatus, Location, SeverityLevel, TriState


def test_earthquake_data_model() -> None:
    now = datetime.utcnow()
    model = EarthquakeData(
        source="TREM-Lite",
        origin_time=now,
        epicenter_location="Taipei",
        magnitude_value=5.3,
        focal_depth=10.0,
        shaking_area=[
            ShakingArea(county_name=Location.TAIPEI, area_intensity=3.0),
        ],
    )
    assert model.source == "TREM-Lite"
    assert model.origin_time == now
    assert isinstance(model.id, UUID)
    assert model.shaking_area[0].county_name == Location.TAIPEI


def test_earthquake_alert_alias_serialization() -> None:
    now = datetime.utcnow()
    alert = EarthquakeAlert(
        id="eq-001",
        source="TREM-Lite",
        origin_time=now,
        location=Location.TAIPEI,
        severity_level=SeverityLevel.L1,
        status=AlertStatus.OPEN,
        has_damage=TriState.UNKNOWN,
        needs_command_center=TriState.UNKNOWN,
        processed_time=None,
        processing_duration=45,
    )

    dumped = alert.model_dump(by_alias=True)
    assert dumped["originTime"] == alert.origin_time
    assert dumped["status"] == AlertStatus.OPEN.value
    assert dumped["hasDamage"] == TriState.UNKNOWN.value
    assert dumped["needsCommandCenter"] == TriState.UNKNOWN.value


def test_invalid_enum_raises_error() -> None:
    now = datetime.utcnow()
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        EarthquakeEvent(
            id="eq-002",
            source="TREM-Lite",
            origin_time=now,
            location="INVALID_LOCATION",
            severity_level=SeverityLevel.L1,
        )
