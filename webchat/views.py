import logging
from typing import Any, Optional, Dict

import anyio
from marshmallow import Schema, fields
from marshmallow.validate import OneOf
from starlette.types import Scope, Receive, Send
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette_web.common.channels.base import Channel
from starlette_web.common.utils import get_random_string
from starlette_web.common.ws.base_endpoint import BaseWSEndpoint
from starlette_web.contrib.redis.channel_layers import RedisPubSubChannelLayer
from starlette_web.common.conf import settings


logger = logging.getLogger("starlette_web.tests")


class ChatRequestSchema(Schema):
    request_type = fields.Str(
        validate=[
            OneOf(["connect", "publish"]),
        ]
    )
    room = fields.Str(required=False)
    message = fields.Str(required=False)


class ChatWebsocketTestEndpoint(BaseWSEndpoint):
    request_schema = ChatRequestSchema

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        super().__init__(scope, receive, send)
        self._manager_lock = anyio.Lock()
        self._response_handler_init = False
        self._channels_init = False
        self._channels_wrap: Optional[Channel] = None
        self._channels: Optional[Channel] = None
        self._tasks = set()
        self._active_response_handlers = set()

    async def _register_background_task(self, task_id: str, websocket: WebSocket, data: Dict):
        async with self._manager_lock:
            if not self._channels_init and data["request_type"] == "connect":
                redis_options = settings.CHANNEL_LAYERS["redispubsub"]["OPTIONS"]
                # TODO try other channels
                self._channels_wrap = Channel(RedisPubSubChannelLayer(**redis_options))
                self._channels = await self._channels_wrap.__aenter__()
                self._channels_init = True

            self._tasks.add(task_id)

    async def _background_handler(self, task_id: str, websocket: WebSocket, data: Dict):
        async with self._manager_lock:
            if not self._channels_init:
                logger.debug("No initialized channels detected. Quit handler")
                return

        if data["request_type"] == "publish":
            await self._channels.publish(data.get("room", "chatroom"), data["message"])

        elif data["request_type"] == "connect":
            # TODO: examine anyio KeyError due to WeakRef
            # We have to use explicit await here, instead of calling self.task_group.spawn_soon
            # since otherwise this _background_handler will close, call _unregister and close
            # the task_group altogether, since no other tasks are spawned at this moment
            #await self._run_dialogue(websocket, data.get("room", "chatroom"))
            dialog_task_id = get_random_string(50)
            self._tasks.add(dialog_task_id)
            self.task_group.start_soon(self._run_dialogue, websocket, data.get("room", "chatroom"), dialog_task_id)

        else:
            raise WebSocketDisconnect(code=1005, reason="Invalid request type")

    async def _unregister_background_task(
        self, task_id: str, websocket: WebSocket, task_result: Any
    ):
        async with self._manager_lock:
            self._tasks.discard(task_id)

            if self._channels_init and not self._tasks:
                await self._channels_wrap.__aexit__(None, None, None)
                self._channels_init = False

    async def _run_dialogue(self, websocket: WebSocket, room: str, dialog_chat_id: str):
        print(room, id(self))
        try:
            async with self._manager_lock:
                if room in self._active_response_handlers:
                    return
                self._active_response_handlers.add(room)

            async with self._channels.subscribe(room) as subscriber:
                async for event in subscriber:
                    await websocket.send_json(event.message)
        finally:
            self._tasks.discard(dialog_chat_id)
            async with self._manager_lock:
                self._active_response_handlers.discard(room)
