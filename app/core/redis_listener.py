import json

from app.websockets.manager import manager

from .redis import redis_client


async def listen_to_alerts() -> None:
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("alerts")

    async for msg in pubsub.listen():
        if msg["type"] == "message":
            data = json.loads(msg["data"])
            await manager.broadcast(data)
