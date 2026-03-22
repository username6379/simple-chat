from src.chat.storage import RedisChatStorage
from src.redis_client import client
from src.session.storage import RedisSessionStorage


async def get_chat_storage():
    return RedisChatStorage(client=client)


async def get_session_storage():
    return RedisSessionStorage(client=client)
