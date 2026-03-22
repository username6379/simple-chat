from fastapi import WebSocket


async def maintain_connection(websocket: WebSocket):
    while True:
        data = await websocket.receive()

        if data:
            await websocket.send({'type': 'error', 'message': 'This route does not support any commands.'})
