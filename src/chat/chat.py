import asyncio
from fastapi.websockets import WebSocketDisconnect, WebSocket
from src.chat.messages_router import get_message_router, MessagesRouter


class Chat:
    def __init__(self, id, messages_router: MessagesRouter):
        self.id = id
        self.messages_router = messages_router
        self.sessions = {}  # {session_id: (websocket, tasks)}

    async def broadcast_locally(self, payload):
        """ Send payload to the sessions that are in current chat instance. Must be called by the messages router """
        for session_values in self.sessions.values():
            await session_values[0].send_json(payload)

    async def broadcast_globally(self, payload):
        """ Send payload to the broker, messages routers will pick up message
        and will call the chat broadcast_locally method to send message to the users """
        await self.messages_router.publish(self.id, payload)

    async def add_session(self, session_id, websocket):
        self.sessions[session_id] = (websocket, asyncio.create_task(self.__listen_to_websocket(session_id, websocket)))
        await self.broadcast_globally(
            {'type': 'event', 'data': {'type': 'join', 'content': f'{session_id} joined chat!'}}
        )

    async def remove_session(self, session_id):
        self.sessions[session_id][1].cancel()
        del self.sessions[session_id]
        await self.broadcast_globally(
            {'type': 'event', 'data': {'type': 'quit', 'content': f'{session_id} quit chat!'}}
        )

    async def __listen_to_websocket(self, session_id, websocket: WebSocket):
        try:
            while True:
                data = await websocket.receive_json()
                content = data.get('content')
                if not content:
                    await websocket.send_json({'type': 'error', 'message': 'Missing or empty "content" key'})
                else:
                    await self.broadcast_globally(
                        {'type': 'message', 'data': {'sender': session_id, 'content': content}}
                    )
        except WebSocketDisconnect as e:
            await self.remove_session(session_id)


chats = {}


async def get_chat(chat_id):
    chat = chats.get(chat_id)

    if chat:
        return chat

    messages_router = get_message_router(chat_id)
    chat = Chat(chat_id, messages_router)
    chats[chat.id] = chat
    await messages_router.subscribe(chat)
    return chat


async def wait_chat_websocket_disconnect(session_id, chat):
    try:
        await chat.sessions[session_id][1]
    except asyncio.CancelledError:
        await chat.remove_session(session_id)
