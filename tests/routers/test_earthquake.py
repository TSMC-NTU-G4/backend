import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytz
from httpx import AsyncClient

from app.main import app
from app.models.earthquake import EarthquakeAlert, EarthquakeData, ShakingArea
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


@pytest.mark.asyncio
@patch("app.routers.earthquake.update_alert_metrics", autospec=True)
async def test_process_earthquake_alert(
    mock_update_metrics: AsyncMock,
    mock_redis_methods: dict[str, AsyncMock],
) -> None:
    alert_id = "123"
    # override the mock return value inside the fixture
    mock_redis_methods["get"].return_value = True  # Simulate alert exists in Redis

    alert_payload = EarthquakeAlert(
        id=alert_id,
        source="TREM-Lite",
        origin_time=datetime(2024, 5, 22, 10, 0, 0),
        location=Location.TAIPEI,
        severity_level=SeverityLevel.L1,
        status=AlertStatus.PROCESSED,
        has_damage=TriState.TRUE,
        needs_command_center=TriState.TRUE,
        processed_time=datetime(2024, 5, 22, 10, 1, 0),
        processing_duration=60,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            f"/api/earthquake/alerts/{alert_id}",
            json=json.loads(alert_payload.model_dump_json()),
        )

    assert response.status_code == 200
    parsed = response.json()

    assert parsed["message"] == "Processed alert 123 successfully"

    mock_update_metrics.assert_called_once()
    mock_redis_methods["delete"].assert_awaited_once()


@pytest.mark.asyncio
@patch("app.routers.earthquake.get_data_by_prefix", new_callable=AsyncMock)
@patch("app.routers.earthquake.update_alert_autoclose_metrics")
async def test_autoclose_expired_alerts(
    mock_update_metrics: AsyncMock,
    mock_get_data: AsyncMock,
    mock_redis_methods: dict[str, AsyncMock],
) -> None:
    taipei_tz = pytz.timezone("Asia/Taipei")
    old_time = datetime.now(taipei_tz) - timedelta(hours=2)

    mock_get_data.return_value = [
        EarthquakeAlert(
            id="1",
            source="TREM-Lite",
            origin_time=old_time,
            location=Location.TAIPEI,
            severity_level=SeverityLevel.L1,
            status=AlertStatus.OPEN,
            has_damage=TriState.UNKNOWN,
            needs_command_center=TriState.UNKNOWN,
            processed_time=old_time,
            processing_duration=0,
        ),
    ]

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete("/api/earthquake/alerts/autoclose")

    assert response.status_code == 200
    assert "Auto-closed 1 expired alerts" in response.json()["message"]
    mock_update_metrics.assert_called_once()
    mock_redis_methods["delete"].assert_awaited_once()
    mock_redis_methods["publish"].assert_awaited_once()


@pytest.mark.asyncio
@patch("app.routers.earthquake.fetch_realtime_data", new_callable=AsyncMock)
@patch("app.routers.earthquake.process_earthquake_data", new_callable=AsyncMock)
async def test_get_realtime_earthquake_data(
    mock_process: AsyncMock,
    mock_fetch: AsyncMock,
    mock_redis_methods: dict[str, AsyncMock],
) -> None:
    # 模擬真實的地震資料
    taipei_tz = pytz.timezone("Asia/Taipei")
    mock_fetch.return_value = EarthquakeData(
        source="TREM-Lite",
        origin_time=datetime.now(taipei_tz),
        epicenter_location="",
        magnitude_value=4.5,
        focal_depth=10.0,
        shaking_area=[
            ShakingArea(county_name="Taipei", area_intensity=2.5),
            ShakingArea(county_name="Hsinchu", area_intensity=0.0),
        ],
    )

    # Mock returned alerts from processing
    mock_process.return_value = [
        # Dummy alert with just minimal valid fields
        type(
            "DummyAlert",
            (),
            {
                "model_dump_json": lambda self, **kwargs: json.dumps({"id": "abc"}),
                "source": "TREM-Lite",
                "location": type("Location", (), {"value": "Taipei"}),
                "id": "abc",
            },
        )(),
    ]

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/earthquake/realtime")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Realtime earthquake data fetched successfully"
    assert "data" in body
    # 驗證回傳的資料格式是否正確
    assert body["data"]["source"] == "TREM-Lite"
    assert len(body["data"]["shakingArea"]) == 2
    assert body["data"]["shakingArea"][0]["countyName"] == "Taipei"
    assert body["data"]["shakingArea"][0]["areaIntensity"] == 2.5

    # Ensure redis publish is called with expected structure
    mock_redis_methods["publish"].assert_called()
    args, _ = mock_redis_methods["publish"].call_args
    assert args[0] == "alerts"
    payload = json.loads(args[1])
    assert payload["type"] == AlertStatus.OPEN
