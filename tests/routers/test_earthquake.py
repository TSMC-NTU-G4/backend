from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.main import app
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
