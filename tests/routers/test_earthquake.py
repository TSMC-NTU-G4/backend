from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.models.response import Response as APIResponse


@patch("app.routers.earthquake.process_earthquake_data")
def test_create_earthquake(
    mock_process: MagicMock,
    client: TestClient,
) -> None:
    earthquake_payload = {
        "source": "test",
        "origin_time": "2024-01-01T12:00:00Z",
        "epicenter_location": "Taipei",
        "magnitude_value": 5.5,
        "focal_depth": 4.0,
        "shaking_area": [],
    }
    response = client.post("/api/earthquake/", json=earthquake_payload)
    assert response.status_code == 200

    parsed = APIResponse(**response.json())
    assert "Created earthquake" in parsed.message

    mock_process.assert_called_once()
