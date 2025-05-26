import time
from unittest.mock import AsyncMock, patch

import pytest

from app.utils import realtime_data_handler as rdh


@pytest.mark.asyncio
@patch("app.utils.realtime_data_handler.httpx.AsyncClient")
async def test_fetch_data_success(mock_async_client_class: AsyncMock) -> None:
    # Create a mock response object
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()  # no exception thrown
    mock_response.json = AsyncMock(return_value={"data": "ok"})

    # Create a mock client instance whose get() returns the mock_response
    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response

    # Setup context manager __aenter__ to return the mock client instance
    mock_async_client_class.return_value.__aenter__.return_value = mock_client_instance

    # Call the function
    response = await rdh.fetch_data("https://example.com", timeout_ms=1000)

    # Assert the return value is the mocked response object
    assert response == mock_response

    # And assert calling json() on it returns expected dict
    json_data = await response.json()
    assert json_data == {"data": "ok"}


@pytest.mark.asyncio
@patch("app.utils.realtime_data_handler.fetch_data")
async def test_get_station_info_with_fresh_cache(mock_fetch_data: AsyncMock) -> None:
    # Setup cached data and timestamp within interval
    rdh.station_info = {"cached": "data"}
    rdh.last_station_info_fetch = time.time() * 1000  # now, fresh

    result = await rdh.get_station_info()
    assert result == rdh.station_info
    mock_fetch_data.assert_not_called()  # should not fetch again


@pytest.mark.asyncio
@patch("app.utils.realtime_data_handler.fetch_data")
async def test_get_station_info_fetch_none(mock_fetch_data: AsyncMock) -> None:
    rdh.station_info = None
    rdh.last_station_info_fetch = 0
    mock_fetch_data.return_value = None

    result = await rdh.get_station_info()
    assert result is None
