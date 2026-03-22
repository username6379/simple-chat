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
        """ Create chat reference and notify users that new user joined """
        await self.session_storage.create_chat_reference(chat_id=self.chat_id, session_id=self.session_id)
        await self.stream.notify_join()
        return (await self._initialize_listening()), (await self._initialize_publishing())

    async def disconnect(self):
        """ Delete chat reference and notify other users about quit """
        await self.session_storage.remove_chat_reference(self.session_id)
        await self.stream.notify_quit()