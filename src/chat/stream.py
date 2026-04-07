import json
from abc import ABC, abstractmethod
from redis.asyncio.client import PubSub


class ChatStream(ABC):
    """
    Abstract class for actions in chat.
    These methods could be declared in ChatConnection however then I would have half of defined and half of not defined methods
    """
    def __init__(self, chat_id: int, session_id: int):
        self.chat_id = chat_id
        self.session_id = session_id

    @abstractmethod
    async def listen(self):
        """ Must be implemented as async generator """
        pass

    @abstractmethod
    async def notify_join(self):
        """ Notify chat about new session joining """
        pass

    @abstractmethod
    async def notify_quit(self):
        """ Notify chat about a session leaving """
        pass

    @abstractmethod
    async def publish_message(self, content: str):
        """ Publish message in stream """
        pass


class ChatStreamProducer(ABC):
    @abstractmethod
    def produce(self, chat_id: int, session_id: int) -> ChatStream:
        pass


from redis.asyncio import Redis


class RedisChatStream(ChatStream):
    def __init__(self, client: Redis, pubsub: PubSub,  *args, **kwargs):
        self.__client = client
        self.__pubsub = pubsub
        super().__init__(*args, **kwargs)

    async def listen(self):
        await self.__pubsub.subscribe(f'chat:{self.chat_id}:stream')

        # TODO remove duplicated code
        try:
            async for data in self.__pubsub.listen():
                if data['type'] == 'subscribe':
                    continue
                yield json.loads(data['data'])
        except BaseException as e:
            await self.__pubsub.aclose()
            raise e

    async def notify_join(self):
        message = json.dumps({
            'type': 'notification',
            'info': {
                'type': 'join',
                'session_id': self.session_id
            }
        })
        await self.__client.publish(f'chat:{self.chat_id}:stream', message)

    async def notify_quit(self):
        message = json.dumps({
            'type': 'notification',
            'info': {
                'type': 'quit',
                'session_id': self.session_id
            }
        })
        await self.__client.publish(f'chat:{self.chat_id}:stream', message)

    async def publish_message(self, content: str):
        message = json.dumps({
            'type': 'message',
            'content': content,
            'session_id': self.session_id
        })
        await self.__client.publish(f'chat:{self.chat_id}:stream', message)


class RedisChatStreamProducer(ChatStreamProducer):
    __chats = {}

    def __init__(self, client: Redis):
        self.client = client

    def produce(self, chat_id: str, session_id: int) -> ChatStream:
        return RedisChatStream(client=self.client, chat_id=chat_id, session_id=session_id)