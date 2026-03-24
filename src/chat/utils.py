from fastapi.websockets import WebSocket, WebSocketDisconnect
from src.chat.stream import ChatStream
from src.base.exceptions import ClientDisconnect
from src.session.storage import SessionStorage


async def handle_input_from_chat_stream(websocket: WebSocket, chat_stream: ChatStream):
    try:
        async for data in chat_stream.listen():  # .listen() is a async generator. Don't take in consideration the warning
            if data['type'] == 'message':
                if data['session_id'] != chat_stream.session_id:
                    await websocket.send_json(data)

            elif data['type'] == 'notification':
                if data['info']['type'] == 'quit' and data['info']['session_id'] == chat_stream.session_id:
                    raise ClientDisconnect
                await websocket.send_json(data)
    except WebSocketDisconnect:
        raise ClientDisconnect


async def handle_input_to_chat_stream(websocket: WebSocket, chat_stream: ChatStream, session_storage: SessionStorage):
    try:
        while True:
            data = await websocket.receive_json()

            if await session_storage.is_session_alive(chat_stream.session_id):
                await chat_stream.publish_message(content=data['content'])

    except WebSocketDisconnect:
        raise ClientDisconnect