import json
from asyncio import CancelledError
from redis.asyncio import Redis
from src.base.redis import client


class MessagesRouterState:
    IDLE = 0
    ROUTING = 1


# TODO abstract implementation
class MessagesRouter:
    def __init__(self, client: Redis):
        self.__client = client
        self.__pubsub = client.pubsub()
        self.subscribers = {}
        self.__state = MessagesRouterState.IDLE

    async def subscribe(self, chat):
        self.subscribers[chat.id] = chat
        await self.__pubsub.subscribe(f'chat:{chat.id}:messages')

    async def unsubscribe(self, chat):
        del self.subscribers[chat.id]
        await self.__pubsub.unsubscribe(f'chat:{chat.id}:messages')

    async def start_routing(self):
        if self.__state == MessagesRouterState.ROUTING:
            raise ValueError('Router is already in routing state.') # Change to right type of error

        try:
            async for data in self.__pubsub.listen():
                if data['type'] == 'subscribe':
                    continue
                ...
        except CancelledError:
            self.__state = MessagesRouterState.IDLE

    async def publish(self, chat_id, payload):
        await self.__client.publish(f'chat:{chat_id}:messages', json.dumps({'chat_id': chat_id, 'payload': payload}))


message_routers = [
    MessagesRouter(client)
]


def get_message_router(chat_id):
    return message_routers[0]
