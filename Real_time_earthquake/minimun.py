import asyncio
import websockets

async def listen():
    uri = "ws://localhost:2487"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            print(f"Received: {message}")
            exit()

# Run the async loop
asyncio.run(listen())
