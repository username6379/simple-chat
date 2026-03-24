from src.base.redis import client
from src.session.storage import RedisSessionStorage
from src.chat.stream import RedisChatStreamProducer
from src.session.stream import RedisSessionLifeStreamProducer


async def get_session_storage():
    return RedisSessionStorage(client=client)


async def get_chat_stream_producer():
    return RedisChatStreamProducer(client=client)


async def get_session_life_stream_producer():
    return RedisSessionLifeStreamProducer(client=client)
