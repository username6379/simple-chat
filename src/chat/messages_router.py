import asyncio
import json
import re
from abc import abstractmethod, ABC
from redis.asyncio import Redis
from src.base.redis import client


class MessagesRouter(ABC):
    def __init__(self):
        self.subscribers = {}
        self.__routing_task = asyncio.create_task(self.start_routing())

    async def subscribe(self, chat):
        self.subscribers[chat.id] = chat

    async def unsubscribe(self, chat):
        del self.subscribers[chat.id]

    @abstractmethod
    async def start_routing(self):
        pass

    @abstractmethod
    async def publish(self, chat_id, payload):
        pass


class RedisMessagesRouter(MessagesRouter):
    def __init__(self, client: Redis):
        self.__client = client
        self.__pubsub = client.pubsub()
        super().__init__()

    async def subscribe(self, chat):
        await super().subscribe(chat)
        await self.__pubsub.subscribe(f'chat:{chat.id}:messages')

    async def unsubscribe(self, chat):
        await super().unsubscribe(chat)
        await self.__pubsub.unsubscribe(f'chat:{chat.id}:messages')

    async def start_routing(self):
        async for data in self.__pubsub.listen():
            if data['type'] == 'message':
                chat_id = re.search(r'chat:(\d+):messages', data['channel']).group(1)
                asyncio.create_task(
                    self.subscribers[chat_id].broadcast_locally(data=json.loads(data['data']))
                )

    async def publish(self, chat_id, payload: dict):
        await self.__client.publish(f'chat:{chat_id}:messages', json.dumps(payload))


message_router = RedisMessagesRouter(client)


def get_messages_router(chat_id):
    return message_router
