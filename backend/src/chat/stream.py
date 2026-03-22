class ChatStream:
    async def listen(self):
        pass

    async def notify_join(self, session_id: int):
        pass

    async def notify_quit(self, session_id: int):
        pass

    async def publish_message(self, content: str, session_id: int):
        pass

    async def publish_session_death_event(self):
        pass