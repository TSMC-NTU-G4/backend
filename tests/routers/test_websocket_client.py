from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocketDisconnect


@pytest.fixture
def mock_websocket_setup() -> dict[str, Any]:
    """Provides a mock websocket and connection manager."""
    mock_websocket = AsyncMock()
    mock_manager = MagicMock(connect=AsyncMock(), disconnect=MagicMock())
    return {"websocket": mock_websocket, "manager": mock_manager}


class TestWebSocketHandler:
    """Test suite for WebSocket alerts functionality."""

    @pytest.mark.asyncio
    async def test_default_ping_interval(
        self,
        mock_websocket_setup: dict[str, Any],
    ) -> None:
        mocks = mock_websocket_setup
        with (
            patch(
                "asyncio.sleep",
                side_effect=[None, Exception("Test completed")],
            ) as mock_sleep,
            patch("app.websockets.alerts_ws.manager", mocks["manager"]),
            patch("app.websockets.alerts_ws.get_ping_interval", return_value=60),
        ):
            from app.websockets.alerts_ws import alerts_websocket

            with pytest.raises(Exception, match="Test completed"):
                await alerts_websocket(mocks["websocket"])

        mocks["manager"].connect.assert_called_once_with(mocks["websocket"])
        mocks["websocket"].send_text.assert_called_with("ping")
        assert mocks["websocket"].send_text.call_count >= 1
        mock_sleep.assert_called_with(60)

    @pytest.mark.asyncio
    async def test_custom_ping_interval(
        self,
        mock_websocket_setup: dict[str, Any],
    ) -> None:
        mocks = mock_websocket_setup
        with (
            patch(
                "asyncio.sleep",
                side_effect=[None, Exception("Test completed")],
            ) as mock_sleep,
            patch("app.websockets.alerts_ws.manager", mocks["manager"]),
            patch("app.websockets.alerts_ws.get_ping_interval", return_value=5),
        ):
            from app.websockets.alerts_ws import alerts_websocket

            with pytest.raises(Exception, match="Test completed"):
                await alerts_websocket(mocks["websocket"])

        mock_sleep.assert_called_with(5)

    @pytest.mark.asyncio
    async def test_disconnect_handling(
        self,
        mock_websocket_setup: dict[str, Any],
    ) -> None:
        mocks = mock_websocket_setup
        mocks["websocket"].send_text.side_effect = WebSocketDisconnect()
        with (
            patch("app.websockets.alerts_ws.manager", mocks["manager"]),
            patch("app.websockets.alerts_ws.get_ping_interval", return_value=60),
        ):
            from app.websockets.alerts_ws import alerts_websocket

            await alerts_websocket(mocks["websocket"])

        mocks["manager"].connect.assert_called_once_with(mocks["websocket"])
        mocks["manager"].disconnect.assert_called_once_with(mocks["websocket"])

    @pytest.mark.asyncio
    async def test_multiple_ping_cycles(
        self,
        mock_websocket_setup: dict[str, Any],
    ) -> None:
        mocks = mock_websocket_setup
        with (
            patch(
                "asyncio.sleep",
                side_effect=[None, None, None, Exception("Test completed")],
            ) as mock_sleep,
            patch("app.websockets.alerts_ws.manager", mocks["manager"]),
            patch("app.websockets.alerts_ws.get_ping_interval", return_value=1),
        ):
            from app.websockets.alerts_ws import alerts_websocket

            with pytest.raises(Exception, match="Test completed"):
                await alerts_websocket(mocks["websocket"])

        assert mocks["websocket"].send_text.call_count == 4
        mocks["websocket"].send_text.assert_called_with("ping")
        mock_sleep.assert_called_with(1)

    @pytest.mark.asyncio
    async def test_connect_called_before_ping(
        self,
        mock_websocket_setup: dict[str, Any],
    ) -> None:
        mocks = mock_websocket_setup
        call_order = []

        async def track_connect(ws: Any) -> None:
            call_order.append("connect")

        async def track_send_text(msg: str) -> None:
            call_order.append("send_text")
            raise Exception("Test completed")

        mocks["manager"].connect.side_effect = track_connect
        mocks["websocket"].send_text.side_effect = track_send_text

        with (
            patch("app.websockets.alerts_ws.manager", mocks["manager"]),
            patch("app.websockets.alerts_ws.get_ping_interval", return_value=60),
        ):
            from app.websockets.alerts_ws import alerts_websocket

            with pytest.raises(Exception, match="Test completed"):
                await alerts_websocket(mocks["websocket"])

        assert call_order == ["connect", "send_text"]
