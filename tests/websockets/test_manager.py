from unittest.mock import AsyncMock, MagicMock

import pytest

from app.websockets.manager import WebSocketManager


@pytest.mark.asyncio
async def test_connect_adds_websocket_to_connections() -> None:
    mock_ws = AsyncMock()
    manager = WebSocketManager()

    await manager.connect(mock_ws)

    mock_ws.accept.assert_awaited_once()
    assert mock_ws in manager.connections


def test_disconnect_removes_websocket_from_connections() -> None:
    mock_ws = MagicMock()
    manager = WebSocketManager()
    manager.connections.append(mock_ws)

    manager.disconnect(mock_ws)

    assert mock_ws not in manager.connections


def test_disconnect_does_nothing_if_not_connected() -> None:
    mock_ws = MagicMock()
    manager = WebSocketManager()

    # Should not raise any error
    manager.disconnect(mock_ws)
    assert mock_ws not in manager.connections


@pytest.mark.asyncio
async def test_broadcast_sends_message_to_all_connections() -> None:
    mock_ws_1 = AsyncMock()
    mock_ws_2 = AsyncMock()

    manager = WebSocketManager()
    manager.connections = [mock_ws_1, mock_ws_2]

    message = {"event": "earthquake", "magnitude": 5.2}
    await manager.broadcast(message)

    mock_ws_1.send_json.assert_awaited_once_with(message)
    mock_ws_2.send_json.assert_awaited_once_with(message)
