from fastapi.websockets import WebSocket, WebSocketDisconnect
from src.exceptions import ChatLeave, SessionDied
from src.session.storage import SessionStorage


async def start_listening_state(websocket: WebSocket, session_id: int, stream: ChatStream):
    await stream.notify_join(session_id)

    try:
        while True:
            data = await stream.listen()

            if data['type'] == 'message':
                if data['session_id'] != session_id:
                    await websocket.send_json(data)

            elif data['type'] == 'notification':
                if data['info']['type'] == 'quit' and data['info']['session_id'] == session_id:
                    return

            elif data['type'] == 'system':
                if data['info']['session_end']:
                    raise SessionDied
    except WebSocketDisconnect:
        raise ChatLeave


async def start_publishing_state(websocket: WebSocket, session_id, session_storage: SessionStorage, stream: ChatStream):
    try:
        while True:
            data = await websocket.receive_json()

            if await session_storage.is_session_alive(session_id):
                await stream.publish_message(content=data['content'], session_id=session_id)
            else:
                raise SessionDied
    except WebSocketDisconnect:
        raise ChatLeave