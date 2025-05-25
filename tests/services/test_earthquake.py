import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.models.earthquake import EarthquakeData, ShakingArea
from app.models.enums import Location, SeverityLevel
from app.services.earthquake import (
    classify_severity,
    generate_alerts,
    generate_events,
    process_earthquake_data,
)


@pytest.fixture
def sample_earthquake_data() -> EarthquakeData:
    return EarthquakeData(
        id=str(uuid.uuid4()),
        source="CWB",
        origin_time=datetime.utcnow(),
        epicenter_location="Taipei",
        magnitude_value=5.2,
        focal_depth=1.0,
        shaking_area=[
            ShakingArea(county_name=Location.TAIPEI, area_intensity=4),
            ShakingArea(county_name=Location.TAINAN, area_intensity=2),
        ],
    )


@pytest.mark.asyncio
async def test_generate_alerts(sample_earthquake_data: EarthquakeData) -> None:
    events = generate_events(sample_earthquake_data)
    with (
        patch(
            "app.services.earthquake.get_alert_suppress_time",
            new=AsyncMock(return_value=300),
        ),
        patch(
            "app.services.earthquake.get_data_by_prefix",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.services.earthquake.redis_client.set",
            new=AsyncMock(),
        ) as mock_redis_set,
    ):
        alerts = await generate_alerts(events)
        assert alerts
        assert all(alert.severity_level != SeverityLevel.NA for alert in alerts)
        assert mock_redis_set.await_count == len(alerts)


@pytest.mark.asyncio
async def test_process_earthquake_data(sample_earthquake_data: EarthquakeData) -> None:
    with (
        patch("app.services.earthquake.observe_earthquake_data"),
        patch("app.services.earthquake.observe_earthquake_events"),
        patch("app.services.earthquake.observe_earthquake_alerts"),
        patch(
            "app.services.earthquake.get_alert_suppress_time",
            new=AsyncMock(return_value=300),
        ),
        patch(
            "app.services.earthquake.get_data_by_prefix",
            new=AsyncMock(return_value=[]),
        ),
        patch("app.services.earthquake.redis_client.set", new=AsyncMock()),
    ):
        alerts = await process_earthquake_data(sample_earthquake_data)
        assert isinstance(alerts, list)


@pytest.mark.parametrize(
    ("magnitude", "intensity", "expected"),
    [
        (6.0, 0, SeverityLevel.L2),
        (4.5, 3, SeverityLevel.L2),
        (3.5, 2, SeverityLevel.L1),
        (2.0, 0, SeverityLevel.NA),
    ],
)
def test_classify_severity(
    magnitude: float,
    intensity: float,
    expected: SeverityLevel,
) -> None:
    assert classify_severity(magnitude, intensity) == expected
