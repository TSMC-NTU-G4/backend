import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import websockets

from .manager import WebSocketManager

router = APIRouter()

earthquake_manager = WebSocketManager()

async def fetch_earthquake_data(earthquake_server_url: str):
    """Continuously fetch earthquake data from an external server via WebSocket."""
    while True:
        try:
            async with websockets.connect(earthquake_server_url) as ws:
                while True:
                    try:
                        message = await ws.recv()
                        # Assuming the server sends JSON data
                        data = json.loads(message)
                        # await earthquake_manager.broadcast(data)
                        # print the data
                        # print(data)
                        
                    except json.JSONDecodeError:
                        # Handle malformed JSON
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        # Connection closed, break inner loop to reconnect
                        break
        except Exception as e:
            # Connection error, retry after delay
            print(f"WebSocket connection error: {e}")
            await asyncio.sleep(5)

@router.websocket("/ws/earthquake")
async def earthquake_websocket(websocket: WebSocket) -> None:
    await earthquake_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        earthquake_manager.disconnect(websocket)

# Task to run the earthquake data fetcher
earthquake_fetcher_task = None

def start_earthquake_fetcher(server_url: str):
    """Start the task to fetch earthquake data."""
    global earthquake_fetcher_task
    if earthquake_fetcher_task is None or earthquake_fetcher_task.done():
        earthquake_fetcher_task = asyncio.create_task(fetch_earthquake_data(server_url)) 