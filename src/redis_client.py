from redis.asyncio import Redis


client = Redis(host='localhost', port=8001, max_connections=50)


async def get_redis_connection():
    yield client
