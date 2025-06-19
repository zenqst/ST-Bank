from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from utils.states import Interaction, Buy_Boxes
from data.datebase import advanced_interaction, last_interaction, get_profile, items, buy_boxes, advanced_buy_boxes, hu_number

from keyboards import inline, reply
from keyboards.inline import ActionCallback, CurrencyCallback

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
    balance = get_profile(user_id, username)

    data = await state.get_data()
    await state.set_state(Interaction.currency)
    await bot.answer_callback_query(call.id)

    currency = callback_data.currency
    await state.update_data(currency=currency)

    if data['type'] == "buy":
        text = f"Введите количество {currency.upper()}, которое вы хотите приобрести (Баланс: {balance[0]}₽ ({hu_number(balance[0])}))"
    else:
        balance_index = 1 if currency == "ST" else 2
        currency_balance = balance[balance_index]
        text = f"Введите количество {currency.upper()}, которое вы хотите продать (Баланс: {currency_balance}{currency.upper()} ({hu_number(balance[0])}))"

    await state.set_state(Interaction.amount)
    await call.message.edit_text(text, reply_markup=inline.cancel_button)

@router.callback_query()
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username
    balance = get_profile(user_id, username)

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

    if call.data == 'items':
        await bot.answer_callback_query(call.id)
        await items(user_id, username, call, inline)

    if call.data == 'return_profile':
        data = get_profile(user_id, username)
        await call.message.edit_text(f'📋 Профиль пользователя @{username}\n\n<b>ID:</b> {user_id}\n<b>Рубли:</b> {data[0]} ({hu_number(data[0])})\n<b>ST:</b> {data[1]} ({hu_number(data[1])})\n<b>V:</b> {data[2]} ({hu_number(data[2])})\n📦: {data[3]} ({hu_number(data[3])})', reply_markup=inline.profile_buttons)

    if call.data == 'buy_box':
        await state.set_state(Buy_Boxes.pcs)
        await call.message.edit_text(f'Введите количество Боксов 📦, которое вы хотите приобрести (Баланс: {balance[1]}ST ({hu_number(balance[1])})')
        await bot.answer_callback_query(call.id)
    
    if call.data == 'agree_buy_box':
        data = await state.get_data()
        text = buy_boxes(user_id, username, data['pcs'])
        await bot.answer_callback_query(call.id)
        await call.message.edit_text(text, reply_markup=None)
        await state.clear()

@router.message(Interaction.amount)
async def amount_handler(message: Message, state: FSMContext):
    await advanced_interaction(state, message)

@router.message(Buy_Boxes.pcs)
async def buy_box(message: Message, state: FSMContext):
    await advanced_buy_boxes('Box', state, message, inline)

