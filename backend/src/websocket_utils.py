import json
from redis.asyncio.client import PubSub
from fastapi import WebSocket, WebSocketDisconnect


async def handle_incoming_chat_messages(session_id: int, websocket: WebSocket, pubsub: PubSub):
    try:
        async for data in pubsub.listen():
            channel = data['channel'].decode('utf-8')

            # Stop listening if session died
            if channel == f'session:{session_id}:life':
                return

            dict_message = json.loads(data['data'].decode('utf-8'))

            # End task if current user quit
            if dict_message['type'] == 'quit' and dict_message['session_id'] == session_id:
                return

            # Don't send to the current user his own message
            if dict_message['type'] == 'message' and dict_message['session_id'] == session_id:
                continue

            await websocket.send_json(dict_message)
    except WebSocketDisconnect:
        await pubsub.aclose()


async def maintain_session_life(websocket: WebSocket):
    while True:
        data = await websocket.receive()

        if data:
            await websocket.send({'type': 'error', 'message': 'This route does not support any commands.'})

