import asyncio
from fastapi.websockets import WebSocket
from src.chat.storage import ChatStorage
from src.chat.states import start_listening_state, start_publishing_state
from src.chat.stream import ChatStream
from src.session.storage import SessionStorage


class ChatConnection:
    def __init__(
            self,
            session_id,
            chat_id,
            websocket: WebSocket,
            chat_storage: ChatStorage,
            session_storage: SessionStorage,
            stream: ChatStream,
    ):
        self.session_id = session_id
        self.chat_id = chat_id
        self.websocket = websocket
        self.stream = stream
        self.chat_storage = chat_storage
        self.session_storage = session_storage

    async def _initialize_listening(self) -> asyncio.Task:
        """ Creates task that listens to stream and sends messages to user """
        return asyncio.create_task(start_listening_state(
            websocket=self.websocket,
            stream=self.stream,
            session_id=self.session_id
        ))

    async def _initialize_publishing(self) -> asyncio.Task:
        """ Creates task that listens to websocket and publish to stream """
        return asyncio.create_task(start_publishing_state(
            websocket=self.websocket,
            stream=self.stream,
            session_storage=self.session_storage,
            session_id=self.session_id
        ))

    async def connect(self) -> tuple[asyncio.Task, asyncio.Task]:
        await self.storage.create_chat_reference()
        await self.stream.notify_join(self.session_id)
        return (await self._initialize_listening()), (await self._initialize_publishing())

    async def disconnect(self):
        """ Execute something when user disconnects from chat """
        await self.storage.remove_chat_reference(self.chat_id, self.session_id)
        await self.stream.notify_quit(self.session_id)