from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from utils.states import Interaction, Donate
from data.datebase import advanced_interaction, last_interaction, open_box, get_profile, get_price, items, hu_number
from callbacks.donations import send_invoice_handler

from keyboards import inline, reply
from keyboards.inline import ActionCallback, CurrencyCallback, BoxCallback

router = Router()

@router.callback_query(ActionCallback.filter())
async def action_type_handler(call: CallbackQuery, callback_data: ActionCallback, bot: Bot, state: FSMContext):
    if callback_data.action_type in ("buy", "sell"):
        await state.set_state(Interaction.type)
        await state.update_data(type=callback_data.action_type)
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.from_user.id, 'Выберите валюту:', reply_markup=inline.choose_currency_buttons)

@router.callback_query(CurrencyCallback.filter())
async def currency_handler(call: CallbackQuery, callback_data: CurrencyCallback, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username
    balance = await get_profile(user_id, username)

    data = await state.get_data()
    await state.set_state(Interaction.currency)
    await bot.answer_callback_query(call.id)

    currency = callback_data.currency
    await state.update_data(currency=currency)

    if data['type'] == "buy":
        text = f"Введите количество {currency.upper()}, которое вы хотите приобрести (Баланс: {balance[0]}₽ ({await hu_number(balance[0])}))"
    else:
        balance_index = 1 if currency == "ST" else 2
        currency_balance = balance[balance_index]
        text = f"Введите количество {currency.upper()}, которое вы хотите продать (Баланс: {currency_balance}{currency.upper()} ({await hu_number(balance[0])}))"

    await state.set_state(Interaction.amount)
    await call.message.edit_text(text, reply_markup=inline.cancel_button)

@router.callback_query(BoxCallback.filter())
async def boxes_handler(call: CallbackQuery, callback_data: BoxCallback, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username
    balance = await get_profile(user_id, username)
    currency_balance = balance[3]

    if callback_data.type == "opening":
        await bot.answer_callback_query(call.id)
        await call.message.delete()
        await open_box(id = user_id, username = username, message = call.message, amount = callback_data.amount)
    else:
        await state.set_state(Interaction.type)
        await state.update_data(type = "buy")

        await state.set_state(Interaction.currency)
        await state.update_data(currency = "box")

        await bot.answer_callback_query(call.id)

        price = await get_price("box")

        await state.set_state(Interaction.amount)
        await call.message.edit_text(f"Введите количество Боксов, которое вы хотите купить (Баланс: {currency_balance} 📦 | {balance[1]}ST)\n\n1 📦 = {price[0]}ST", reply_markup=inline.cancel_button)

@router.callback_query()
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username
    balance = await get_profile(user_id, username)

    if call.data == "agree":
        data = await state.get_data()
        text = await last_interaction(user_id, username, state)
        await bot.answer_callback_query(call.id)
        await call.message.edit_text(text, reply_markup=None)
        await state.clear()

    if call.data == "cancel":
        await state.clear()
        await call.message.delete()
        await bot.send_message(call.from_user.id, '✅ <b>Транзакция отменена</b>', reply_markup=reply.main)

    if call.data == "donate":
        await state.set_state(Donate.amount)
        await bot.answer_callback_query(call.id)

        await call.message.edit_text('❓ <b>Введите кол-во валюты, которое вы хотите приобрести</b>', reply_markup=inline.cancel_button)

    if call.data == 'items':
        await bot.answer_callback_query(call.id)
        await items(user_id, username, call, inline)

    if call.data == 'return_profile':
        data = await get_profile(user_id, username)
        await call.message.edit_text(f'📋 Профиль пользователя @{username}\n\n<b>ID:</b> {user_id}\n<b>Рубли:</b> {data[0]} ({await hu_number(data[0])})\n<b>ST:</b> {data[1]} ({await hu_number(data[1])})\n<b>V:</b> {data[2]} ({await hu_number(data[2])})\n📦: {data[3]} ({await hu_number(data[3])})', reply_markup=inline.profile_buttons)

@router.message(Interaction.amount)
async def interaction_amount_handler(message: Message, state: FSMContext):
    await advanced_interaction(state, message)

@router.message(Donate.amount)
async def donate_amount_handler(message: Message, state: FSMContext):
    await send_invoice_handler(state, message)