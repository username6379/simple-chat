import asyncio
from src.session.death_dispatcher import get_session_death_dispatcher

async def wait_session_death(session_id):
    dispatcher = await get_session_death_dispatcher(session_id)
    event = asyncio.Event()
    await dispatcher.subscribe(session_id, event)
    await event.wait()
