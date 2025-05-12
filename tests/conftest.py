from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_redis_methods() -> Generator[dict[str, AsyncMock]]:
    with (
        patch("app.core.redis.redis_client.set", new_callable=AsyncMock) as mock_set,
        patch("app.core.redis.redis_client.get", new_callable=AsyncMock) as mock_get,
        patch("app.core.redis.redis_client.scan", new_callable=AsyncMock) as mock_scan,
    ):
        mock_get.return_value = None
        mock_scan.return_value = (0, [])

        yield {
            "set": mock_set,
            "get": mock_get,
            "scan": mock_scan,
        }
