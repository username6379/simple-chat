import asyncio
import re
from abc import ABC, abstractmethod
from src.base.redis import client


class SessionsDeathsDispatcher(ABC):
    def __init__(self):
        self.subscribers = {}
        self.__monitoring_task = asyncio.create_task(self.monitor())

    async def subscribe(self, session_id):
        """ Add session id to the self.subscribers and create an asyncio event (if none exist) for the session.
         The created event will be returned and client can await it, it will be set when death notification will arrive.
         """
        event = self.subscribers.get(session_id)

        if event:
            return event

        event = asyncio.Event()
        self.subscribers[session_id] = event
        return event

    async def unsubscribe(self, session_id):
        self.subscribers[session_id].set()
        del self.subscribers

    @abstractmethod
    async def monitor(self):
        """ Must be called only once.
         Starts listening to some source for incoming session death notifications """
        pass

    @abstractmethod
    async def stop(self):
        self.__monitoring_task.cancel()
        await self.__monitoring_task

    @abstractmethod
    async def publish(self, session_id):
        """ Publish session death """
        pass


# TODO
#  In case of using redis cluster: what if 1 session dispatcher will take care of managing the routing from multiple nodes,
#  it will create async tasks, assign to them pubsubs, and just will listen to these pubsubs.
class RedisSessionsDeathsDispatcher(SessionsDeathsDispatcher):
    def __init__(self, client):
        self.__client = client
        self.__pubsub = client.pubsub()
        super().__init__()

    async def subscribe(self, session_id):
        event = await super().subscribe(session_id)
        await self.__pubsub.subscribe(f'session_death:{session_id}')
        return event

    async def unsubscribe(self, session_id):
        await super().unsubscribe(session_id)
        await self.__pubsub.unsubscribe(f'session_death:{session_id}')

    async def monitor(self):
        async for data in self.__pubsub.listen():
            if data['type'] == 'message':
                session_id = re.search(r'session_death:(\d+)', data['channel']).group(1)
                asyncio.create_task(self.unsubscribe(session_id))

    async def publish(self, session_id):
        await self.__client.publish(f'session_death:{session_id}', 1)


dispatcher = RedisSessionsDeathsDispatcher(client)

async def get_sessions_deaths_dispatcher(session_id):
    return dispatcher
