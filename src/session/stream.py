import json
from abc import ABC, abstractmethod
from redis.asyncio import Redis


class SessionLifeStream(ABC):
    def __init__(self, session_id):
        self.session_id = session_id

    @abstractmethod
    async def listen(self):
        pass

    @abstractmethod
    async def notify_about_death(self):
        pass


class SessionLifeStreamProducer(ABC):
    @abstractmethod
    def produce(self, session_id: int) -> SessionLifeStream:
        pass


class RedisSessionLifeStream(SessionLifeStream):
    def __init__(self, client: Redis, *args, **kwargs):
        self.__client = client
        super().__init__(*args, **kwargs)

    async def listen(self):
        pubsub = self.__client.pubsub()
        await pubsub.subscribe(f'session:{self.session_id}:life')

        try:
            async for data in pubsub.listen():
                if data['type'] == 'subscribe':
                    continue
                yield json.loads(data['data'])
        except Exception as e:
            await pubsub.aclose()
            raise e

    async def notify_about_death(self):
        await self.__client.publish(f'session:{self.session_id}:life', json.dumps({'type': 'dead'}))


class RedisSessionLifeStreamProducer(SessionLifeStreamProducer):
    def __init__(self, client: Redis):
        self.client = client

    def produce(self, session_id: int) -> SessionLifeStream:
        return RedisSessionLifeStream(client=self.client, session_id=session_id)
