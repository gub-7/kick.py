from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, AsyncIterator

from kick.categories import Category
from kick.emotes import Emote

from .assets import Asset
from .chatroom import Chatroom
from .livestream import Livestream
from .object import BaseDataclass, HTTPDataclass
from .utils import cached_property
from .videos import Video

if TYPE_CHECKING:
    from .types.user import InnerUser, UserPayload

__all__ = ("User", "Socials")


class Socials(BaseDataclass["InnerUser"]):
    @property
    def instagram(self) -> str:
        return self._data["instagram"]

    @property
    def youtube(self) -> str:
        return self._data["youtube"]

    @property
    def twitter(self) -> str:
        return self._data["twitter"]

    @property
    def discord(self) -> str:
        return self._data["discord"]

    @property
    def tiktok(self) -> str:
        return self._data["tiktok"]

    @property
    def facebook(self) -> str:
        return self._data["facebook"]


class User(HTTPDataclass["UserPayload"]):
    @property
    def id(self) -> int:
        return self._data["user_id"]

    @property
    def slug(self) -> str:
        return self._data["slug"]

    @property
    def vod_enabled(self) -> bool:
        return self._data["vod_enabled"]

    @property
    def is_banned(self) -> bool:
        return self._data["is_banned"]

    @property
    def subscription_enabled(self) -> bool:
        return self._data["subscription_enabled"]

    @property
    def follower_count(self) -> int:
        return self._data["followers_count"]

    @property
    def subscriber_badges(self) -> list:
        """THIS IS RAW DATA"""
        return self._data["subscriber_badges"]

    @property
    def follower_badges(self) -> list:
        """THIS IS RAW DATA"""
        return self._data["follower_badges"]

    @cached_property
    def online_banner_url(self) -> Asset | None:
        return (
            Asset(url=self._data["banner_image"]["url"], http=self.http)
            if self._data["banner_image"]
            else None
        )

    @cached_property
    def offline_banner_url(self) -> Asset | None:
        return (
            Asset._from_asset_src(
                data=self._data["offline_banner_image"], http=self.http
            )
            if self._data["offline_banner_image"]
            else None
        )

    @property
    def is_muted(self) -> bool:
        return self._data["muted"]

    @property
    def is_verified(self) -> bool:
        return self._data["verified"]

    @property
    def avatar_url(self) -> str:
        return self._data["user"]["profile_pic"]

    @property
    def can_host(self) -> bool:
        return self._data["can_host"]

    @property
    def bio(self) -> str:
        return self._data["user"]["bio"]

    @property
    def agreed_to_terms(self) -> bool:
        return self._data["user"]["agreed_to_terms"]

    @cached_property
    def email_verified_at(self) -> datetime:
        return datetime.fromisoformat(self._data["user"]["email_verified_at"])

    @property
    def username(self) -> str:
        return self._data["user"]["username"]

    @property
    def country(self) -> str:
        return self._data["user"]["country"]

    @property
    def state(self) -> str:
        return self._data["user"]["state"]

    @cached_property
    def socials(self) -> Socials:
        return Socials(data=self._data["user"])

    @cached_property
    def livestream(self) -> Livestream:
        return Livestream(data=self._data["livestream"], http=self.http)

    @cached_property
    def chatroom(self) -> Chatroom:
        chatroom = Chatroom(data=self._data["chatroom"], http=self.http)
        chatroom.streamer = self
        return chatroom

    @cached_property
    def recent_categories(self) -> list[Category]:
        return [
            Category(data=c, http=self.http) for c in self._data["recent_categories"]
        ]

    async def fetch_videos(self) -> list[Video]:
        data = await self.http.get_streamer_videos(self.slug)
        return [Video(data=v, http=self.http) for v in data]

    async def fetch_emotes(
        self, *, include_global: bool = False
    ) -> AsyncIterator[Emote]:
        data = await self.http.get_emotes(self.slug)
        for emote in data[2]["emotes"]:
            yield Emote(data=emote, http=self.http)
        if include_global is True:
            for emote in data[1]["emotes"]:
                yield Emote(data=emote, http=self.http)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return other.id == self.id
        else:
            return False

    def __str__(self) -> str:
        return self.username
