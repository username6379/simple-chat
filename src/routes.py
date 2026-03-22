import asyncio
import json

from starlette.responses import JSONResponse
from src.app import app
from fastapi import WebSocket, Depends, Body
from fastapi.websockets import WebSocketDisconnect

from src.data_handlers import listen_to_chat
from src.redis_client import get_redis_connection
from src.utils import generate_session_id, generate_chat_id
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

        # If session with generated id already exists
        if await storage.get(f'session:{session_id}'):
            continue
        else:
            await storage.set(f'session:{session_id}', value=1)
            break

    try:
        # Return generated session id to user
        await websocket.send({'session_id': session_id})

        # Maintain connection
        while True:
            data = await websocket.receive()

            if data:
                await websocket.send({'message': 'This route does not support any commands.'})

    except WebSocketDisconnect:
        await storage.delete(f'session:{session_id}')


@app.post('/chat')
async def create_chat(
        session_id: str = Body(),
        storage: Redis = Depends(get_redis_connection)
):
    while True:
        chat_id = generate_chat_id()

        # If chat with generated id already exists
        if await storage.get(f'chat:{chat_id}'):
            continue
        else:
            await storage.set(f'chat:{chat_id}', value=1)
            await storage.set(f'session:{session_id}:chat_reference', chat_id)
            break

    return JSONResponse(content={'chat_id': chat_id})


@app.websocket('/chat')
async def chat_connection(
        websocket: WebSocket,
        storage: Redis = Depends(get_redis_connection)
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

    # Check if user is in any other chat
    if await storage.get(f'session:{session_id}:chat_reference'):
        await websocket.close(reason='Not possible to be in 2 or more chats simultaneously')

    pubsub = storage.pubsub()

    await pubsub.subscribe(f'chat:{chat_id}:stream')

    # Notify members about new user
    await storage.publish(
        f'chat:{chat_id}:stream',
        json.dumps({'type': 'notification', 'content': f'User {session_id} joined.'})
    )

    # Create task to send messages to current user
    asyncio.create_task(listen_to_chat(websocket, pubsub))

    # Listen to current users for messages
    try:
        while True:
            data = await websocket.receive_json()

            await storage.publish(
                f'chat:{chat_id}:stream',
                json.dumps({'type': 'message', 'author': session_id, 'content': data})
            )

    except WebSocketDisconnect:
        await storage.delete(f'session:{session_id}:chat_reference')
        await storage.publish(
            f'chat:{chat_id}:stream',
            json.dumps({'type': 'notification', 'content': f'User {session_id} quit.'})
        )



# TODO add current users info
# TODO when last user disconnects the listen_to_chat task doesn't have a way to end
# TODO add simple frontend