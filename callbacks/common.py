from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards import inline, reply
router = Router()

@router.callback_query()
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username

    if call.data == "cancel":
        await state.clear()
        await call.message.edit_text('✅ <b>Действие отменено</b>')