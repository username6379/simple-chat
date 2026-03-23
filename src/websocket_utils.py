from fastapi import WebSocket


async def maintain_connection(websocket: WebSocket):
    while True:
        await websocket.receive_json()
        await websocket.send({'type': 'error', 'message': 'This route does not support any commands.'})
