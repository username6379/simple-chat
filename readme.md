## Table of content
- About application
- Installation
- Startup
- Routes
- Future improvements


### About application
simple-chat is a straightforward, real-time chat application built as a monolithic backend.
It leverages the speed of FastAPI, the pub/sub capabilities of Redis, and WebSockets for seamless, instant communication.

However, I did my best to design it in a such way that would be easy to swap Redis pub/sub with any other message broker.
This can be done because of abstract class "ChatStream" and "ChatStorage, implement using your beloved message broker.

The application is designed to be lightweight, with a strict and predictable approach to how users connect and interact
within chat rooms.

With great sadness, at the moment the application doesn't have frontend and any testing suite.


### Installation
```
git clone https://github.com/username6379/simple-chat . 
```

### Start up
```
docker compose up -d
```

### Routes
***/session***
> By connecting to this route you will receive the session id. Response: **{"session_id": session_id}**

> Disruption to the connection will mean session invalidation.

> Any further commands to this websocket will return same response which is: **{'type': 'error', 'message': 'This route does not support any commands.'}**

***/chat***
> By connecting to this route you will join a chat. However, before joining chat you will need to send the chat id which you want to join and your session id.
> Request data: **{"chat_id": chat_id, "session_id": session_id}**

> Request data for sending message: **{"content": your_message}**

> Response when someone sent a message in chat: **{"type": "message", ""}**

> Response when someone joined: **{"type": "notification", "info": {"type": "join", "session_id": session_id}}**

> Response when someone quit: **{"type": "notification", "info": {"type": "quit", "session_id": session_id}}**  

### Future improvements
- To be able to pull current count of users in chat and their session ids
- Add test suite
- Add frontend

