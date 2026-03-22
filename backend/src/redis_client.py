from redis.asyncio import Redis


client = Redis(host='storage', port=6379, max_connections=50)


async def get_redis_connection():
    yield client
