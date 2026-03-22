from fastapi.websockets import WebSocket, WebSocketDisconnect
from src.session.exceptions import SessionDied
from src.chat.exceptions import ChatLeave
from src.chat.stream import ChatStream
from src.session.storage import SessionStorage

# TODO add some kind of dataclass for incoming data because accessing the keys in such way is error prone
# TODO handle somehow case where message for some reason didn't send. notify user about this
async def start_listening_state(websocket: WebSocket, session_id: int, stream: ChatStream):
    try:
        while True:
            async for data in stream.listen(): # .listen() is a async generator. Don't take in consideration the warning
                if data['type'] == 'message':
                    if data['session_id'] != session_id:
                        await websocket.send_json(data)

                elif data['type'] == 'notification':
                    if data['info']['type'] == 'quit' and data['info']['session_id'] == session_id:
                        raise ChatLeave
                    await websocket.send_json(data)

                elif data['type'] == 'session_death' and data['session_id'] == session_id:
                    raise SessionDied
    except WebSocketDisconnect:
        raise ChatLeave


async def start_publishing_state(websocket: WebSocket, session_id, session_storage: SessionStorage, stream: ChatStream):
    try:
        while True:
            data = await websocket.receive_json()

            if await session_storage.is_session_alive(session_id):
                await stream.publish_message(content=data['content'])
            else:
                raise SessionDied
    except WebSocketDisconnect:
        raise ChatLeave