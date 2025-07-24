from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import TelegramObject
from cachetools import TTLCache


class AntifloodMiddleware(BaseMiddleware):
    cache: TTLCache[str, bool]
    warned_users: TTLCache[int, bool]
    
    def __init__(self, time_limit: int = 2, warn_cooldown: int = 10) -> None:
        self.cache = TTLCache(maxsize=10000, ttl=time_limit)
        self.warned_users = TTLCache(maxsize=10000, ttl=warn_cooldown)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        throttling_key = get_flag(data, "throttling_key") or "antiflood"

        user_id = None
        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
        elif hasattr(event, "message") and event.message and event.message.from_user:
            user_id = event.message.from_user.id
        else:
            return await handler(event, data)

        key = f"{throttling_key}:{user_id}"

        if key in self.cache:
            if user_id not in self.warned_users:
                self.warned_users[user_id] = True
                if hasattr(event, "answer"):
                    await event.answer("😣 <b>Немного передохните, я уже устал...</b>\n\n<i>Сообщения принимаются с небольшим к/д</i>")
            return
        else:
            self.cache[key] = True

        return await handler(event, data)