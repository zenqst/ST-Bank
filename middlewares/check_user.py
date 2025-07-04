from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from database.queries import check_profile
from states.enums import UserStatus
from keyboards.inline import register_buttons

class UserCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not hasattr(event, 'from_user'):
            return await handler(event, data)
        
        user_id = event.from_user.id
        status = await check_profile(user_id)
        
        if status == UserStatus.NOT_FOUND:
            if isinstance(event, (Message, CallbackQuery)):
                msg = event if isinstance(event, Message) else event.message
                await msg.answer(
                    "⚠️ <b>Вы ещё не зарегистрировались!</b>",
                    reply_markup=register_buttons
                )
            
            if isinstance(event, CallbackQuery):
                await event.answer()
            
            return
        
        return await handler(event, data)