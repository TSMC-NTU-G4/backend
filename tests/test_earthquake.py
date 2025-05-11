# tests/test_earthquake.py
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.core.redis.redis_client.scan", return_value=(0, []))
@patch("app.core.redis.redis_client.get", return_value=None)
@patch("app.core.redis.redis_client.set")
def test_create_earthquake(mock_set: Any, mock_get: Any, mock_scan: Any) -> None:
    payload = {
        "source": "sensor_A",
        "origin_time": "2024-01-01T12:00:00Z",
        "epicenter_location": "Taipei",
        "magnitude_value": 5.5,
        "focal_depth": 4.0,
        "shaking_area": [],
    }

    response = client.post("/api/earthquake/", json=payload)
    assert response.status_code == 200
    assert "data" in response.json()
    assert "message" in response.json()
