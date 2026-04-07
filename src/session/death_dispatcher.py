import asyncio
import re

from src.base.redis import client


class SessionsDeathsDispatcher:
    def __init__(self, client):
        self.__client = client
        self.__pubsub = client.pubsub()
        self.subscribers = {}

    async def subscribe(self, session_id, notify_event):
        self.subscribers[session_id] = notify_event
        await self.__pubsub.subscribe(f'session_death:{session_id}')

    async def unsubscribe(self, session_id):
        self.subscribers[session_id].set()
        del self.subscribers
        await self.__pubsub.unsubscribe(f'session_death:{session_id}')

    async def monitor(self):
        async for data in self.__pubsub.listen():
            if data['type'] == 'message':
                session_id = re.search(r'session_death:(\d+)', data['channel']).group(1)
                asyncio.create_task(self.unsubscribe(session_id))

    async def publish(self, session_id):
        await self.__client.publish(f'session_death:{session_id}', 1)


dispatcher = SessionsDeathsDispatcher(client)

async def get_session_death_dispatcher(session_id):
    return dispatcher
