from redis.asyncio import Redis

# class RedisClient:
#     __client = None
#
#     def __new__(cls, *args, **kwargs):
#         if not cls.__client:
#             cls.__client = Redis(host='redis-instance', port=6379, max_connections=50, decode_responses=True)
#         return
#
#     def close(self):
#         self.__client.aclose()

# TODO add some mechanism of creating only clients that are needed
client = Redis(host='redis-instance', port=6379, max_connections=50, decode_responses=True)
