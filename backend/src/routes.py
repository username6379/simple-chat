import asyncio

from src.app import app
from fastapi import WebSocket, Depends
from fastapi.websockets import WebSocketDisconnect
from src.chat.connection import ChatConnection
from src.chat.storage import ChatStorage
from src.chat.exceptions import ChatLeave
from src.session.exceptions import SessionDied
from src.session.storage import SessionStorage
from src.websocket_utils import maintain_session_life
from src.redis_client import get_redis_connection
from src.utils import generate_session_id
from redis.asyncio import Redis



@app.websocket('/session')
async def session(
        websocket: WebSocket,
        storage: Redis = Depends(get_redis_connection)
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

        if not await storage.get(f'session:{session_id}'):
            await storage.set(f'session:{session_id}', value=1)
            break

    try:
        await websocket.send({'session_id': session_id})
        await maintain_session_life(websocket)
    except WebSocketDisconnect:
        # Delete session and notify about its end of lifespan
        await storage.delete(f'session:{session_id}')
        await storage.publish(f'session:{session_id}:life', 'end')


# @app.post('/chat')
# async def create_chat(
#         session_id: str = Body(),
#         storage: Redis = Depends(get_redis_connection)
# ):
#     while True:
#         chat_id = generate_chat_id()
#
#         # If chat with generated id already exists
#         if await storage.get(f'chat:{chat_id}'):
#             continue
#         else:
#             await storage.set(f'chat:{chat_id}', value=1)
#             await storage.set(f'session:{session_id}:chat_reference', chat_id)
#             break
#
#     return JSONResponse(content={'chat_id': chat_id})


# @app.websocket('/chat')
# async def chat_connection(
#         websocket: WebSocket,
#         storage: Redis = Depends(get_redis_connection)
# ):
#     await websocket.accept()
#
#     # Get the session_id and chat_id
#     while True:
#         data = await websocket.receive_json()
#         session_id, chat_id = data.get('session_id'), data.get('chat_id')
#
#         if not session_id and not chat_id:
#             await websocket.send_json({'type': 'error', 'message': 'Missing session_id and chat_id'})
#             continue
#         elif not session_id:
#             await websocket.send_json({'type': 'error', 'message': 'Missing session_id'})
#             continue
#         elif not chat_id:
#             await websocket.send_json({'type': 'error', 'message': 'Missing chat_id and chat_id'})
#             continue
#
#     # Check if session is valid
#     if not await storage.get(f'session:{session_id}'):
#         await websocket.close(reason='Unknown session id.')
#
#     # Check if user is in any other chat
#     chat_reference = await storage.get(f'session:{session_id}:chat_reference')
#     if chat_reference and chat_reference != chat_id:
#         await websocket.close(reason='Not possible to be in 2 or more chats simultaneously')
#
#     pubsub = storage.pubsub()
#
#     await pubsub.subscribe(f'chat:{chat_id}:stream', f'session:{session_id}:life')
#
#     # Notify members about new user
#     await storage.publish(
#         f'chat:{chat_id}:stream',
#         json.dumps({'type': 'join', 'session_id': session_id})
#     )
#
#     # Create task to send messages to current user
#     asyncio.create_task(handle_incoming_chat_messages(session_id, websocket, pubsub))
#
#     # Listen to current user for messages
#     try:
#         while True:
#             data = await websocket.receive_json()
#
#             # Check if session still exist
#             if await storage.get(f'session:{session_id}'):
#                 await storage.publish(
#                     f'chat:{chat_id}:stream',
#                     json.dumps({'type': 'message', 'session_id': session_id, 'content': data})
#                 )
#             else:
#                 # If session connection was closed
#                 raise WebSocketDisconnect
#
#     except WebSocketDisconnect:
#         # Delete reference of session to the chat and notify chat members that current session quited
#         await storage.delete(f'session:{session_id}:chat_reference')
#         await storage.publish(
#             f'chat:{chat_id}:stream',
#             json.dumps({'type': 'quit', 'session_id': session_id})
#         )


@app.websocket('/chat')
async def connect_to_chat(
        websocket: WebSocket,
        chat_storage: ChatStorage,
        session_storage: SessionStorage
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

    # Check if session is valid
    if not await session_storage.is_session_alive(session_id):
        await websocket.close(reason='Unknown session id.')

    # Check if session is in any other chat
    chat_reference = await session_storage.get_reference(session_id)

    if chat_reference:
        await websocket.close(reason='Not possible to be in 2 or more chats simultaneously.')

    stream = await chat_storage.get_stream(chat_id)
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

# TODO add current users info
# TODO add simple frontend