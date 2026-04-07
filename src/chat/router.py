import json


class MessagesRouter:
    def __init__(self):
        self.chats = {} # {chat_id: chat}

    def subscribe(self, chat):
        self.chats[chat.id] = chat

    def unsubscribe(self, chat):
        del self.chats[chat.id]

    async def route(self):
        pass

    async def publish(self, chat_id, message):
        pass


class RedisMessagesRouter(MessagesRouter):
    def __init__(self, client):
        self.__client = client
        self.__pubsub = client.pubsub()
        super().__init__()

    async def route(self):
        async for data in self.__pubsub.listen():
            await self.chats.get(data['chat_id']).read_messages_queue.put(data['data'])

    async def publish(self, chat_id, message):
        await self.__client.publish(json.dumps({'chat_id': chat_id, 'data': message}))
