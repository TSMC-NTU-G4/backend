from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.routers.settings import router


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_set_suppress_time(test_app: FastAPI) -> None:
    with patch(
        "app.routers.settings.redis_client.set",
        new_callable=AsyncMock,
    ) as mock_set:
        async with AsyncClient(app=test_app, base_url="http://test") as ac:
            payload = {"alert_suppress_time": 120}
            response = await ac.put("/api/settings/alert-suppress-time", json=payload)

        mock_set.assert_awaited_once_with("ALERT_SUPPRESS_TIME", "120")

        assert response.status_code == 200
        assert response.json() == {
            "message": "Updated to 120 seconds successfully",
            "data": "120",
        }


@pytest.mark.asyncio
async def test_get_suppress_time(test_app: FastAPI) -> None:
    with patch(
        "app.routers.settings.get_alert_suppress_time",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = 180

        async with AsyncClient(app=test_app, base_url="http://test") as ac:
            response = await ac.get("/api/settings/alert-suppress-time")

        mock_get.assert_awaited_once()

        assert response.status_code == 200
        assert response.json() == {
            "message": "The current suppress time is 180 seconds",
            "data": "180",
        }
