from src.chat.stream import ChatStream


class ChatStorage:
    async def get_stream(self, chat_id: int) -> ChatStream:
        pass

    async def create_chat_reference(self, chat_id: int, session_id: int):
        pass

    async def remove_chat_reference(self, chat_id: int, session_id: int):
        pass