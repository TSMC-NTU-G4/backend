from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.models.response import Response as APIResponse


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200

    parsed = APIResponse(**response.json())
    assert parsed.message == "Welcome to the Earthquake API!"
    assert parsed.data is None


@patch("app.main.check_redis_connection", new_callable=AsyncMock)
def test_health_check_healthy(mock_check_redis: AsyncMock, client: TestClient) -> None:
    mock_check_redis.return_value = True

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "message": "All services are healthy",
        "data": {"redis": "healthy"},
    }


@patch("app.main.check_redis_connection", new_callable=AsyncMock)
def test_health_check_unhealthy(
    mock_check_redis: AsyncMock,
    client: TestClient,
) -> None:
    mock_check_redis.return_value = False

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Some services are unhealthy",
        "data": {"redis": "unhealthy"},
    }
