import asyncio
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .manager import manager

router = APIRouter()


def get_ping_interval() -> int:
    return int(os.environ.get("WEBSOCKET_PING_INTERVAL", 60))


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.send_text("ping")
            await asyncio.sleep(get_ping_interval())
    except WebSocketDisconnect:
        manager.disconnect(websocket)
