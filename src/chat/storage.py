from src.chat.stream import ChatStream, RedisChatStream


class ChatStorage:
    async def get_stream(self, chat_id: int, session_id) -> ChatStream:
        pass


from redis.asyncio import Redis


class RedisChatStorage:
    def __init__(self, client: Redis):
        self.__client = client

    async def get_stream(self, chat_id: int, session_id: int) -> RedisChatStream:
        return RedisChatStream(client=self.__client, chat_id=chat_id, session_id=session_id)
