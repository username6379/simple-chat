from src.chat.chat import Chat
from src.chat.messages_router import get_messages_router


class ChatStorage:
    def __init__(self):
        self.chats = {}

    async def get(self, id):
        return self.chats.get(id)

    async def create(self, id):
        messages_router = get_messages_router(id)
        chat = Chat(id=id, messages_router=messages_router)
        self.chats[chat.id] = chat
        await messages_router.subscribe(chat)
        return chat

    async def delete(self, id):
        messages_router = get_messages_router(id)
        await messages_router.unsubscribe(self.chats[id])
        del self.chats[id]


storage = ChatStorage()


def get_chat_storage():
    return storage
