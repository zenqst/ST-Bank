from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards import inline, reply
from database.queries import show_items, send_profile

router = Router()

@router.callback_query()
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username

    if call.data == "cancel":
        await state.clear()
        await bot.answer_callback_query(call.id)
        await call.message.edit_text('✅ <b>Действие отменено</b>')
    
    elif call.data == "items":
        await bot.answer_callback_query(call.id)
        await show_items(user_id, call, inline)

    elif call.data == "return_profile":
        await bot.answer_callback_query(call.id)
        await send_profile(call.from_user.id, call.from_user.username, call)