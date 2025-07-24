from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.queries import send_profile, show_items

router = Router()


@router.callback_query()
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id

    if call.data == "cancel":
        await state.clear()
        await bot.answer_callback_query(call.id)
        await call.message.edit_text('✅ <b>Действие отменено</b>')
    
    elif call.data == "items":
        await bot.answer_callback_query(call.id)
        await show_items(user_id, call)

    elif call.data == "return_profile":
        await bot.answer_callback_query(call.id)
        await send_profile(call.from_user.id, call.from_user.username, call)