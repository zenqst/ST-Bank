from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.queries import edit_currencies_handler, send_prices_msg, send_profile
from keyboards.inline import ReturnCallback
from states.enums import Steps

router = Router()


@router.callback_query(ReturnCallback.filter())
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: ReturnCallback):
    user_id = call.from_user.id
    username = call.from_user.username

    if call.message is None:
        return
    
    if callback_data.prev_step == Steps.PROFILE:
        await bot.answer_callback_query(call.id)
        await send_profile(user_id, username, call)
    elif callback_data.prev_step == Steps.ACTIONS:
        await send_prices_msg(call)
    elif callback_data.prev_step == Steps.CURRENCIES:
        await edit_currencies_handler(state, callback_data, bot, call)