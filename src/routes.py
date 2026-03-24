import asyncio
from src.app import app
from fastapi import WebSocket, Depends
from fastapi.websockets import WebSocketDisconnect
from src.chat.stream import ChatStreamProducer
from src.chat.utils import handle_input_from_chat_stream, handle_input_to_chat_stream
from src.routes_dependencies import get_session_storage, get_chat_stream_producer, get_session_life_stream_producer
from src.session.storage import SessionStorage
from src.session.stream import SessionLifeStreamProducer
from src.base.websocket_utils import maintain_connection
from src.session.utils import handle_input_from_session_life_stream
from src.utils import generate_session_id


@app.websocket('/session')
async def session(
        websocket: WebSocket,
        session_storage: SessionStorage = Depends(get_session_storage),
        session_life_stream_producer: SessionLifeStreamProducer = Depends(get_session_life_stream_producer),
):
    """
        Creates and maintains session.
        If connection to this route is disrupted, session will get invalidated
        and chat to which session is listening (if listening at all) should disrupt connection to this session.
    """
    await websocket.accept()

    # Generate and register session id
    while True:
        session_id = generate_session_id()

        if not await session_storage.is_id_available(session_id):
            await session_storage.save_id(session_id)
            break

    try:
        # Maintain life of session
        await websocket.send_json({'session_id': session_id})
        await maintain_connection(websocket)
    except WebSocketDisconnect:
        # If session connection closed
        # Delete session and notify chat messages handler (if session is in any chat)
        await session_storage.delete_id(session_id)

        chat_reference = await session_storage.get_reference(session_id)

        if chat_reference:
            stream_session_life = session_life_stream_producer.produce(session_id)
            await stream_session_life.notify_about_death()



@app.websocket('/chat')
async def connect_to_chat(
        websocket: WebSocket,
        session_storage: SessionStorage = Depends(get_session_storage),
        chat_stream_producer: ChatStreamProducer = Depends(get_chat_stream_producer),
        session_life_stream_producer: SessionLifeStreamProducer = Depends(get_session_life_stream_producer)
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
    if await session_storage.get_reference(session_id):
        await websocket.close(reason='Not possible to be in 2 or more chats simultaneously.')


    chat_stream = chat_stream_producer.produce(chat_id=chat_id, session_id=session_id)
    session_life_stream = session_life_stream_producer.produce(session_id=session_id)

    await session_storage.create_chat_reference(chat_id=chat_id, session_id=session_id)

    tasks = (
        asyncio.create_task(handle_input_from_session_life_stream(stream=session_life_stream)),
        asyncio.create_task(handle_input_from_chat_stream(websocket=websocket, chat_stream=chat_stream)),
        asyncio.create_task(handle_input_to_chat_stream(websocket=websocket, chat_stream=chat_stream, session_storage=session_storage))
    )

    # Wait for exception such as leaving chat or session death
    _, pending_tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    for pending_task in pending_tasks:
        pending_task.cancel()

    # Remove reference of session to the chat and notify members of chat about quit
    await session_storage.remove_chat_reference(session_id)
    await chat_stream.notify_quit()

# TODO currently /chat creates 2 pubsubs (listening to chat messages and session life) so 2 connections are in use by 1 user. so maybe find a solution to this problem
# TODO add current users info for chat members
