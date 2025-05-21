import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .manager import manager

router = APIRouter()


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.send_text("ping")
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
