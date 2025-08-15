from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from database.user import check_profile
from states.enums import UserStatus


class UserCheckMiddleware(BaseMiddleware):
    def __init__(self):
        self.skip_commands = {"/start", "/shut", "/help"}  # commands for skip checking
        self.skip_messages = {"💲 открыть брокерский счёт"}  # messages for skip checking

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        if isinstance(event, Message):
            if event.from_user is None or event.text is None:
                return
            user_id = event.from_user.id
            text = event.text.lower() or ""
            command = text.split()[0].lower() if text else ""
            if command in self.skip_commands or text in self.skip_messages:
                return await handler(event, data)

            msg = event

        elif isinstance(event, CallbackQuery):
            if not isinstance(event.message, Message):
                return

            user_id = event.from_user.id
            data_str = event.data or ""
            callback_data = data_str.split(":")[0] if data_str else ""
            if callback_data in self.skip_commands or data_str in self.skip_messages:
                return await handler(event, data)

            msg = event.message

        else:
            return await handler(event, data)

        status = await check_profile(user_id)

        if status == UserStatus.NOT_FOUND:
            await msg.answer(
                "⚠️ <b>Вы ещё не зарегистрировались!</b>\n\nПропишите /start",
            )
            if isinstance(event, CallbackQuery):
                await event.answer()
            return None

        data["user_id"] = user_id
        return await handler(event, data)
