from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.main import app
from app.models.earthquake import EarthquakeAlert
from app.models.enums import AlertStatus, Location, SeverityLevel, TriState
from app.models.response import Response as APIResponse


@patch("app.routers.earthquake.process_earthquake_data", new_callable=AsyncMock)
async def test_create_earthquake(mock_process: AsyncMock) -> None:
    mock_process.return_value = []

    payload = {
        "source": "test",
        "origin_time": "2024-01-01T12:00:00Z",
        "epicenter_location": "Taipei",
        "magnitude_value": 5.5,
        "focal_depth": 4.0,
        "shaking_area": [],
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/earthquake/", json=payload)

    assert response.status_code == 200
    parsed = APIResponse(**response.json())
    assert "Created earthquake" in parsed.message
    mock_process.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.routers.earthquake.get_data_by_prefix", new_callable=AsyncMock)
async def test_get_earthquake_alerts(mock_get_data: AsyncMock) -> None:
    mock_alerts = [
        EarthquakeAlert(
            id="1",
            source="TREM-Lite",
            origin_time=datetime(2024, 5, 22, 10, 0, 0),
            location=Location.TAIPEI,
            severity_level=SeverityLevel.L1,
            status=AlertStatus.OPEN,
            has_damage=TriState.UNKNOWN,
            needs_command_center=TriState.UNKNOWN,
            processed_time=datetime(2024, 5, 22, 10, 1, 0),
            processing_duration=60,
        ),
        EarthquakeAlert(
            id="2",
            source="TREM-Lite",
            origin_time=datetime(2024, 5, 21, 9, 0, 0),
            location=Location.HSINCHU,
            severity_level=SeverityLevel.L2,
            status=AlertStatus.OPEN,
            has_damage=TriState.UNKNOWN,
            needs_command_center=TriState.UNKNOWN,
            processed_time=datetime(2024, 5, 21, 9, 2, 0),
            processing_duration=120,
        ),
    ]

    mock_get_data.return_value = mock_alerts

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/earthquake/alerts")

    assert response.status_code == 200
    parsed = response.json()

    assert parsed["message"] == "Found 2 alerts data"
    assert len(parsed["data"]) == 2
    assert parsed["data"][0]["id"] == "1"
    assert parsed["data"][0]["status"] == "OPEN"
    mock_get_data.assert_awaited_once_with("alert", EarthquakeAlert)
