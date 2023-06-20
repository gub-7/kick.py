from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from aiohttp import ClientWebSocketResponse as WebSocketResponse

from .enums import ChatroomChatMode
from .message import Message
from .object import HTTPDataclass
from .utils import cached_property

if TYPE_CHECKING:
    from .chatter import Chatter
    from .http import HTTPClient
    from .types.user import ChatroomPayload
    from .user import User

__all__ = ("Chatroom",)


class ChatroomWebSocket:
    def __init__(self, ws: WebSocketResponse, *, http: HTTPClient):
        self.ws = ws
        self.http = http
        self.send_json = ws.send_json
        self.close = ws.close

    async def poll_event(self) -> None:
        raw_msg = await self.ws.receive()
        msg = raw_msg.json()["data"]
        data = json.loads(msg)

        if data.get("type") in ("message", "reply"):
            msg = Message(data=data)
            self.http.client.dispatch("message", msg)

    async def start(self) -> None:
        while not self.ws.closed:
            await self.poll_event()

    async def subscribe(self, chatroom_id: int) -> None:
        await self.send_json(
            {
                "event": "pusher:subscribe",
                "data": {"auth": "", "channel": f"chatrooms.{chatroom_id}.v2"},
            }
        )

    async def unsubscribe(self, chatroom_id: int) -> None:
        await self.send_json(
            {
                "event": "pusher:unsubscribe",
                "data": {"auth": "", "channel": f"chatrooms.{chatroom_id}.v2"},
            }
        )


class Chatroom(HTTPDataclass["ChatroomPayload"]):
    streamer: User

    @property
    def id(self) -> int:
        return self._data["id"]

    @property
    def chatable_type(self) -> str:
        return self._data["chatable_type"]

    @cached_property
    def created_at(self) -> datetime:
        return datetime.fromisoformat(self._data["created_at"])

    @cached_property
    def updated_at(self) -> datetime:
        return datetime.fromisoformat(self._data["updated_at"])

    @property
    def chat_mode(self) -> ChatroomChatMode:
        return ChatroomChatMode(self._data["chat_mode"])

    @property
    def slowmode(self) -> bool:
        return self._data["slow_mode"]

    @property
    def followers_mode(self) -> bool:
        return self._data["followers_mode"]

    @property
    def subscribers_mode(self) -> bool:
        return self._data["subscribers_mode"]

    @property
    def emotes_mode(self) -> bool:
        return self._data["emotes_mode"]

    @property
    def message_interval(self) -> int:
        return self._data["message_interval"]

    @property
    def following_min_duration(self) -> int:
        return self._data["following_min_duration"]

    async def connect(self) -> None:
        await self.http.ws.subscribe(self.id)

    async def disconnect(self) -> None:
        await self.http.ws.unsubscribe(self.id)

    async def send(self, content: str, /) -> None:
        await self.http.send_message(self.id, content)

    async def fetch_chatter(self, chatter_name: str, /) -> Chatter:
        from .chatter import Chatter

        data = await self.http.get_chatter(self.streamer.slug, chatter_name)
        chatter = Chatter(data=data, http=self.http)
        return chatter

    async def fetch_rules(self) -> str:
        data = await self.http.get_chatroom_rules(self.streamer.slug)
        return data["data"]["rules"]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.id == self.id
