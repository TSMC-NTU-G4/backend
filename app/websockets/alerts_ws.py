from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .manager import manager

router = APIRouter()


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
