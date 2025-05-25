from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.routers.redis import router


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_clear_cache(test_app: FastAPI) -> None:
    # Correct patch path based on your module structure
    with patch(
        "app.routers.redis.redis_client.flushdb",
        new_callable=AsyncMock,
    ) as mock_flushdb:
        async with AsyncClient(app=test_app, base_url="http://test") as ac:
            response = await ac.delete("/api/redis/")

        # Check that the flushdb method was called
        mock_flushdb.assert_awaited_once()

        # Check the response
        assert response.status_code == 200
        assert response.json() == {
            "message": "Clear redis cache successfully",
            "data": None,
        }
