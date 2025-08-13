from asyncio import create_task

from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.text_decorations import html_decoration

from database.core import db
from database.currencies import change_coin, get_price
from database.messages import send_broadcast_message, send_profile
from keyboards.inline import (
    AdminCallback,
    admin_currency_buttons,
    admins_return_buttons,
    cancel_button,
)
from states.enums import Currencies
from states.fsm_states import AdminPanelId, BroadcastText
from utils.control import shutdown
from utils.server_manager import ServerManager

router = Router()
sm = ServerManager()


@router.callback_query(AdminCallback.filter())
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: AdminCallback):
    user_id = call.from_user.id
    username = call.from_user.username

    if call.message is None:
        return
    
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
        
        await call.message.edit_text("📝 Введите ID пользователя")

        await state.set_state(AdminPanelId.user_id)

    elif callback_data.action == "change_coin":
        await bot.answer_callback_query(call.id)
        
        await call.message.edit_text("Выберите валюту", reply_markup=admin_currency_buttons)

    elif callback_data.action in [Currencies.ST.value, Currencies.V.value]:
        await bot.answer_callback_query(call.id)
        
        coin_info = await get_price(callback_data.action, is_round=False)
        
        await call.message.edit_text(f"📝 Введите новую цену {callback_data.action}\n\nТекущая цена: {coin_info['cost']}", reply_markup=admin_currency_buttons)
        await state.set_state(AdminPanelId.coin)
        await state.update_data(coin=callback_data.action)
        await state.set_state(AdminPanelId.amount)

    elif callback_data.action == "start_mailing":
        await bot.answer_callback_query(call.id)
        
        await call.message.edit_text("📝 В следующем сообщении отправьте текст для рассылки")
        await state.set_state(BroadcastText.sending_text)

    elif callback_data.action == "get_logs":
        await bot.answer_callback_query(call.id)
        
        logs = await sm.get_logs()
        await call.message.edit_text("<pre>" + logs + "</pre>", reply_markup=admins_return_buttons)

    elif callback_data.action == "restart_bot":
        await bot.answer_callback_query(call.id)
        
        await call.message.edit_text("🔄 Бот перезапускается...")
        create_task(sm.restart())

    elif callback_data.action == "stop_bot":
        await bot.answer_callback_query(call.id)
        
        await call.message.edit_text("🔴 Бот выключается...")
        create_task(shutdown())


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


@router.message(BroadcastText.sending_text)
async def interaction_amount_handler(message: Message, state: FSMContext, bot: Bot):
    if message.text:
        formatted_text = message.text
    elif message.caption:
        formatted_text = message.caption
    else:
        await message.answer("❌ Пожалуйста, отправьте текст для рассылки")
        return
    
    if message.text and message.entities:
        formatted_text = html_decoration.unparse(message.text, message.entities)
    elif message.caption and message.caption_entities:
        formatted_text = html_decoration.unparse(message.caption, message.caption_entities)
    
    await state.update_data(sending_text=formatted_text)
    await send_broadcast_message(state, bot, message.from_user.id)
