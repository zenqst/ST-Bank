from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.core import db
from database.currencies import change_coin, get_price
from database.messages import send_profile
from keyboards.inline import AdminCallback, admins_return_buttons, admin_currency_buttons, cancel_button
from states.fsm_states import AdminPanelId
from states.enums import Currencies

router = Router()


@router.callback_query(AdminCallback.filter())
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: AdminCallback):
    user_id = call.from_user.id
    username = call.from_user.username

    if call.message is None:
        return

    print(callback_data.action)
    
    if callback_data.action == "get_all_users":
        await bot.answer_callback_query(call.id)
        text = ""

        users = await db.select_data("users", "*", fetch_all=True)

        for i, user in enumerate(users):
            username = user.get("username")
            user_id = user.get("id")
            text += f"{i + 1}. @{username} (<code>{user_id}</code>)\n"
        
        text += f"\nОбщее кол-во пользователей: {len(users)}"
        await call.message.edit_text(text, reply_markup=admins_return_buttons)
    
    elif callback_data.action == "get_user":
        await bot.answer_callback_query(call.id)
        
        await call.message.edit_text("Введите ID пользователя")

        await state.set_state(AdminPanelId.user_id)

    elif callback_data.action == "change_coin":
        await bot.answer_callback_query(call.id)
        
        await call.message.edit_text("Выберите валюту", reply_markup=admin_currency_buttons)

    elif callback_data.action in [Currencies.ST.value, Currencies.V.value]:
        await bot.answer_callback_query(call.id)
        
        coin_info = await get_price(callback_data.action, is_round=False)
        
        await call.message.edit_text(f"Введите новую цену {callback_data.action}\n\nТекущая цена: {coin_info['cost']}", reply_markup=admin_currency_buttons)
        await state.set_state(AdminPanelId.coin)
        await state.update_data(coin=callback_data.action)
        await state.set_state(AdminPanelId.amount)


@router.message(AdminPanelId.user_id)
async def profile_id_handler(message: Message, state: FSMContext):
    user_id = message.text
    await state.update_data(user_id=int(user_id))
    await send_profile(int(user_id), message.from_user.username, message, is_admin=True)
    await state.clear()


@router.message(AdminPanelId.amount)
async def amount_handler(message: Message, state: FSMContext, bot: Bot):
    amount_text = message.text.replace(',', '.')    
    data = await state.get_data()
    
    try:
        amount_float = float(amount_text)

        if amount_float <= 0:
            await message.answer("❌ <b>Пожалуйста, введите положительное число больше 0</b>", reply_markup=cancel_button)
        else:
            await change_coin(data['coin'], bot, amount_float)
            await state.clear()
    except ValueError:
        await message.answer("❌ <b>Пожалуйста, введите корректное число</b>", reply_markup=cancel_button)
        return
