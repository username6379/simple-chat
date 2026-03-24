from abc import abstractmethod, ABC
from redis.asyncio import Redis
from src.session.stream import SessionLifeStream


class SessionStorage(ABC):
    @abstractmethod
    async def is_session_alive(self, session_id: int) -> bool:
        pass

    @abstractmethod
    async def is_id_available(self, session_id: int) -> bool:
        pass

    @abstractmethod
    async def save_id(self, session_id: int):
        pass

    @abstractmethod
    async def delete_id(self, session_id: int):
        pass

    @abstractmethod
    async def get_reference(self, session_id: int) -> int | None:
        """ Returns chat reference (if any) """
        pass

    @abstractmethod
    async def create_chat_reference(self, chat_id: int, session_id: int):
        pass

    @abstractmethod
    async def remove_chat_reference(self, session_id: int):
        pass

    @abstractmethod
    async def get_session_life_stream(self) -> SessionLifeStream:
        pass


class RedisSessionStorage:
    def __init__(self, client: Redis):
        self.__client = client

    async def is_session_alive(self, session_id) -> bool:
        return bool(await self.__client.get(f'session:{session_id}'))

    async def is_id_available(self, session_id: int) -> bool:
        return bool(await self.__client.get(f'session:{session_id}'))

    async def save_id(self, session_id: int):
        await self.__client.set(f'session:{session_id}', 1)

    async def delete_id(self, session_id: int):
        await self.__client.delete(f'session:{session_id}')

    async def get_reference(self, session_id: int) -> int | None:
        return await self.__client.get(f'session:{session_id}:chat_reference')

    async def create_chat_reference(self, chat_id: int, session_id: int):
        await self.__client.set(f'session:{session_id}:chat_reference', chat_id)

    async def remove_chat_reference(self, session_id: int):
        await self.__client.delete(f'session:{session_id}:chat_reference')
