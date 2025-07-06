from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Callable, Awaitable, Dict, Any, Union

from database.queries import check_profile
from states.enums import UserStatus

class UserCheckMiddleware(BaseMiddleware):
    def __init__(self):
        self.skip_commands = {"/start", "/shut"} # commands for skip checking
        self.skip_messages = {"💲 открыть брокерский счёт"} # messages for skip checking

    async def __call__(self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
        ):
        if isinstance(event, Message):
            user_id = event.from_user.id
            text = event.text or ""
            if text.split()[0].lower() in self.skip_commands or self.skip_messages:
                return await handler(event, data)

            msg = event

        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            data_str = event.data or ""
            if data_str.split(":")[0] in self.skip_commands:
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
