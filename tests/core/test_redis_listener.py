import json
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core import redis_listener


@pytest.mark.asyncio
@patch("app.websockets.manager.manager.broadcast", new_callable=AsyncMock)
@patch("app.core.redis_listener.redis_client.pubsub")
async def test_listen_to_alerts(
    mock_pubsub: MagicMock,
    mock_broadcast: AsyncMock,
) -> None:
    fake_pubsub = MagicMock()
    mock_pubsub.return_value = fake_pubsub

    fake_pubsub.subscribe = AsyncMock()

    fake_messages = [
        {"type": "message", "data": json.dumps({"alert": "earthquake detected"})},
        {"type": "message", "data": json.dumps({"alert": "aftershock detected"})},
        {"type": "subscribe", "data": None},
    ]

    async def fake_listen() -> AsyncGenerator[dict]:
        for msg in fake_messages:
            yield msg

    fake_pubsub.listen = fake_listen

    call_args = []
    count = 0

    async def broadcast_side_effect(data: dict) -> None:
        nonlocal count
        call_args.append(data)
        count += 1
        if count >= 2:
            raise StopAsyncIteration

    mock_broadcast.side_effect = broadcast_side_effect

    with pytest.raises(StopAsyncIteration):
        await redis_listener.listen_to_alerts()

    assert count == 2
    assert {"alert": "earthquake detected"} in call_args
    assert {"alert": "aftershock detected"} in call_args
