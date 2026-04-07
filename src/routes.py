import asyncio

from src.app import app
from fastapi import WebSocket, Depends
from fastapi.websockets import WebSocketDisconnect
from src.chat.chat import get_chat, wait_chat_websocket_disconnect
from src.chat.storage import ChatStorage, get_chat_storage
from src.session.storage import get_session_storage
from src.session.dispatcher import get_sessions_deaths_dispatcher
from src.session.storage import SessionStorage
from src.session.utils import wait_session_death
from src.utils import generate_session_id


@app.websocket('/session')
async def session(
        websocket: WebSocket,
        session_storage: SessionStorage = Depends(get_session_storage),
):
    """
        Creates and maintains session.
        If connection to this route is disrupted, session will get invalidated
        and chat to which session is listening (if listening at all) must disrupt connection to this session.
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
        # Maintain connection
        while True:
            await websocket.receive_json()
            await websocket.send({'type': 'error', 'message': 'This route does not support any commands.'})
    except WebSocketDisconnect:
        await session_storage.delete_id(session_id)

        chat_reference = await session_storage.get_reference(session_id)

        if chat_reference:
            sessions_deaths_dispatcher = await get_sessions_deaths_dispatcher(session_id)
            await sessions_deaths_dispatcher.publish(session_id)


@app.websocket('/chat')
async def connect_to_chat(
        websocket: WebSocket,
        session_storage: SessionStorage = Depends(get_session_storage),
        chat_storage: ChatStorage = Depends(get_chat_storage)
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
            await websocket.send_json({'type': 'error', 'message': 'Missing chat_id'})
            continue
        else:
            break

    # Check if session is alive
    if not await session_storage.is_session_alive(session_id):
        await websocket.close(reason='Unknown session id.')

    # Check if session is in any other chat
    if await session_storage.get_reference(session_id):
        await websocket.close(reason='Not possible to be in 2 or more chats simultaneously.')

    # chat = await get_chat(chat_id)
    chat = await chat_storage.get(chat_id)

    if not chat:
        chat = await chat_storage.create(chat_id)

    await chat.add_session(session_id, websocket)

    tasks = [asyncio.create_task(wait_chat_websocket_disconnect(session_id, chat)), asyncio.create_task(wait_session_death(session_id))]

    _, pending_tasks = asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for task in pending_tasks:
        task.cancel()
        await task

    if len(chat.sessions) == 0:
        await chat_storage.delete(chat)


# TODO make incoming data more safe to consume
# TODO add current users info for chat members
