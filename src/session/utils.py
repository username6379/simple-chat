from src.base.exceptions import ClientDisconnect
from src.session.stream import SessionLifeStream


async def handle_input_from_session_life_stream(stream: SessionLifeStream):
    async for data in stream.listen(): # .listen() is a async generator. Don't take in consideration the warning
        if data['type'] == 'dead':
            raise ClientDisconnect