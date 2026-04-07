from src.session.dispatcher import get_sessions_deaths_dispatcher


async def wait_session_death(session_id):
    dispatcher = await get_sessions_deaths_dispatcher(session_id)
    event = await dispatcher.subscribe(session_id)
    await event.wait()
