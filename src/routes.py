import asyncio
from src.app import app
from fastapi import WebSocket, Depends
from fastapi.websockets import WebSocketDisconnect
from src.chat.connection import ChatConnection
from src.chat.storage import ChatStorage
from src.chat.exceptions import ChatLeave
from src.routes_dependencies import get_chat_storage, get_session_storage
from src.session.exceptions import SessionDied
from src.session.storage import SessionStorage
from src.websocket_utils import maintain_connection
from src.utils import generate_session_id


@app.websocket('/session')
async def session(
        websocket: WebSocket,
        session_storage: SessionStorage = Depends(get_session_storage),
        chat_storage: ChatStorage = Depends(get_chat_storage)
):
    """
        Creates and maintains session.
        If connection to this route is disrupted, this means the session is not valid anymore
        and chat to which session is listening (if listening at all) should stop sending messages to this session.
    """
    await websocket.accept()

    # Generate and register session id
    while True:
        session_id = generate_session_id()

        if not await session_storage.is_id_available(session_id):
            await session_storage.save_id(session_id)
            break

    try:
        await websocket.send_json({'session_id': session_id})
        await maintain_connection(websocket)
    except WebSocketDisconnect:
        # If session connection closed
        # Delete session and notify message handler (if session is in any chat)
        await session_storage.delete_id(session_id)

        chat_reference = await session_storage.get_reference(session_id)
        if chat_reference:
            chat_stream = await chat_storage.get_stream(chat_id=chat_reference, session_id=session_id)
            await chat_stream.publish_session_death_event()


@app.websocket('/chat')
async def connect_to_chat(
        websocket: WebSocket,
        chat_storage: ChatStorage = Depends(get_chat_storage),
        session_storage: SessionStorage = Depends(get_session_storage)
):
    await websocket.accept()

    # Get the session_id and chat_id
    while True:
        data = await websocket.receive_json()
        session_id, chat_id = data.get('session_id'), data.get('chat_id')

        if not session_id and not chat_id:
            await websocket.send_json({'type': 'error', 'message': 'Missing session_id and chat_id'})
            continue
        elif not session_id:
            await websocket.send_json({'type': 'error', 'message': 'Missing session_id'})
            continue
        elif not chat_id:
            await websocket.send_json({'type': 'error', 'message': 'Missing chat_id and chat_id'})
            continue
        else:
            break

    # Check if session is valid
    if not await session_storage.is_session_alive(session_id):
        await websocket.close(reason='Unknown session id.')

    # Check if session is in any other chat
    chat_reference = await session_storage.get_reference(session_id)

    if chat_reference:
        await websocket.close(reason='Not possible to be in 2 or more chats simultaneously.')

    stream = await chat_storage.get_stream(chat_id=chat_id, session_id=session_id)
    chat_connection = ChatConnection(
        websocket=websocket,
        session_id=session_id,
        chat_id=chat_id,
        stream=stream,
        chat_storage=chat_storage,
        session_storage=session_storage
    )

    try:
        await asyncio.gather(*(await chat_connection.connect()))
    except ChatLeave, SessionDied:
        await chat_connection.disconnect()

# TODO add current in chat users info
