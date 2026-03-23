import json
from abc import ABC, abstractmethod


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

    @abstractmethod
    async def publish_session_death_event(self):
        """ Maybe move this method somewhere else because it is not quite part of chat stream """
        pass


from redis.asyncio import Redis


class RedisChatStream(ChatStream):
    def __init__(self, client: Redis, *args, **kwargs):
        self.__client = client
        self._pubsub = client.pubsub()
        super().__init__(*args, **kwargs)

    async def listen(self):
        await self._pubsub.subscribe(f'chat:{self.chat_id}:stream', f'session:{self.session_id}:life')

        try:
            async for data in self._pubsub.listen():
                if data['type'] == 'subscribe':
                    continue
                yield json.loads(data['data'])
        except Exception as e:
            await self._pubsub.aclose()
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

    async def publish_session_death_event(self):
        message = json.dumps({
            'type': 'session_death',
            'session_id': self.session_id
        })
        await self.__client.publish(f'chat:{self.chat_id}:stream', message)