class SessionStorage:
    async def is_session_alive(self, session_id):
        pass

    async def get_reference(self, session_id: int) -> int | None:
        """ Returns chat reference (if any) """
        pass
