from redis.asyncio.client import PubSub
from fastapi import WebSocket, WebSocketDisconnect


async def listen_to_chat(websocket: WebSocket, pubsub: PubSub):
    try:
        async for message in pubsub.listen():
            await websocket.send(message)
    except WebSocketDisconnect:
        await pubsub.aclose()
