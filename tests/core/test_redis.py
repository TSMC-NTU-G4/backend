from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

import app.core.redis as redis_module


class DummyModel(BaseModel):
    id: str
    value: int


@pytest.mark.asyncio
@patch("app.core.redis.redis_client.ping", new_callable=AsyncMock)
async def test_check_redis_connection_success(mock_ping: AsyncMock) -> None:
    mock_ping.return_value = True

    result = await redis_module.check_redis_connection()
    assert result is True
    mock_ping.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.core.redis.redis_client.ping", new_callable=AsyncMock)
async def test_check_redis_connection_failure(mock_ping: AsyncMock) -> None:
    mock_ping.side_effect = Exception("Redis down")

    result = await redis_module.check_redis_connection()
    assert result is False
    mock_ping.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.core.redis.redis_client.get", new_callable=AsyncMock)
async def test_get_alert_suppress_time_found(mock_get: AsyncMock) -> None:
    mock_get.return_value = b"300"

    result = await redis_module.get_alert_suppress_time()
    assert result == 300
    mock_get.assert_awaited_once_with("ALERT_SUPPRESS_TIME")


@pytest.mark.asyncio
@patch("app.core.redis.redis_client.get", new_callable=AsyncMock)
async def test_get_alert_suppress_time_not_found(mock_get: AsyncMock) -> None:
    mock_get.return_value = None

    result = await redis_module.get_alert_suppress_time()
    assert result == redis_module.ALERT_SUPPRESS_TIME
    mock_get.assert_awaited_once_with("ALERT_SUPPRESS_TIME")


@pytest.mark.asyncio
@patch("app.core.redis.redis_client.get", new_callable=AsyncMock)
@patch("app.core.redis.redis_client.scan", new_callable=AsyncMock)
async def test_get_data_by_prefix(mock_scan: AsyncMock, mock_get: AsyncMock) -> None:
    # Simulate scan returning one key then done
    mock_scan.side_effect = [(1, [b"test_1"]), (0, [])]

    data_json = '{"id": "1", "value": 42}'
    mock_get.return_value = data_json.encode("utf-8")

    results = await redis_module.get_data_by_prefix("test", DummyModel)

    assert len(results) == 1
    assert isinstance(results[0], DummyModel)
    assert results[0].id == "1"
    assert results[0].value == 42

    assert mock_scan.call_count == 2
    mock_get.assert_awaited_with(b"test_1")
