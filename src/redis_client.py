from redis.asyncio import Redis


client = Redis(host='redis-instance', port=6379, max_connections=50)
