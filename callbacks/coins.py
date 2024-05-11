from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from utils.states import Buy_V, Sell_V, Buy_ST, Sell_ST, Buy_Boxes

from data.datebase import get_price, get_profile, buy_coins, sell_coins, advanced_buy, advanced_sell, items, buy_boxes, advanced_buy_boxes, hu_number

from keyboards import inline

router = Router()

@router.callback_query()
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username
    balance = get_profile(user_id, username)

    if call.data == 'buy':
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.from_user.id, 'Выберите валюту', reply_markup=inline.buy_buttons)
    if call.data == 'sell':
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.from_user.id, 'Выберите валюту', reply_markup=inline.sell_buttons)

    if call.data == 'buy_v':
        await state.set_state(Buy_V.pcs)
        await call.message.edit_text(f'Введите количество V, которое вы хотите приобрести (Баланс: {balance[0]}₽ ({hu_number(balance[0])})')
        await bot.answer_callback_query(call.id)
    if call.data == 'sell_v':
        await state.set_state(Sell_V.pcs)
        await call.message.edit_text(f'Введите количество V, которое вы хотите продать (Баланс: {balance[2]}V ({hu_number(balance[2])})')
        await bot.answer_callback_query(call.id)

    if call.data == 'edit_buy_v':
        await state.set_state(Buy_V.pcs)
        await call.message.edit_text(f'Введите количество V, которое вы хотите приобрести (Баланс: {balance[0]}₽ ({hu_number(balance[0])})', reply_markup=None)
        await bot.answer_callback_query(call.id)
    if call.data == 'edit_sell_v':
        await state.set_state(Sell_V.pcs)
        await call.message.edit_text(f'Введите количество V, которое вы хотите продать (Баланс: {balance[2]}V ({hu_number(balance[2])})', reply_markup=None)
        await bot.answer_callback_query(call.id)
    
    if call.data == 'agree_buy_v':
        data = await state.get_data()
        text = buy_coins(user_id, username, 'V', data['pcs'])
        await call.message.edit_text(text, reply_markup=None)
        await state.clear()

    if call.data == 'agree_sell_v':
        data = await state.get_data()
        text = sell_coins(user_id, username, 'V', data['pcs'])
        await call.message.edit_text(text, reply_markup=None)
        await state.clear()

    
    if call.data == 'buy_st':
        await state.set_state(Buy_ST.pcs)
        await call.message.edit_text(f'Введите количество ST, которое вы хотите приобрести (Баланс: {balance[0]}₽ ({hu_number(balance[0])})')
        await bot.answer_callback_query(call.id)
    if call.data == 'sell_st':
        await state.set_state(Sell_ST.pcs)
        await call.message.edit_text(f'Введите количество ST, которое вы хотите продать (Баланс: {balance[1]}ST ({hu_number(balance[1])})')
        await bot.answer_callback_query(call.id)

    if call.data == 'edit_buy_st':
        await state.set_state(Buy_ST.pcs)
        await bot.answer_callback_query(call.id)
        await call.message.edit_text(f'Введите количество ST, которое вы хотите приобрести (Баланс: {balance[0]}₽ ({hu_number(balance[0])})', reply_markup=None)
    if call.data == 'edit_sell_st':
        await state.set_state(Sell_ST.pcs)
        await bot.answer_callback_query(call.id)
        await call.message.edit_text(f'Введите количество ST, которое вы хотите продать (Баланс: {balance[1]}ST ({hu_number(balance[1])})', reply_markup=None)
    
    if call.data == 'agree_buy_st':
        data = await state.get_data()
        text = buy_coins(user_id, username, 'ST', data['pcs'])
        await bot.answer_callback_query(call.id)
        await call.message.edit_text(text, reply_markup=None)
        await state.clear()

    if call.data == 'agree_sell_st':
        data = await state.get_data()
        text = sell_coins(user_id, username, 'ST', data['pcs'])
        await bot.answer_callback_query(call.id)
        await call.message.edit_text(text, reply_markup=None)
        await state.clear()

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
    if call.data == 'edit_buy_box':
        await state.set_state(Buy_Boxes.pcs)
        await bot.answer_callback_query(call.id)
        await call.message.edit_text(f'Введите количество Боксов 📦, которое вы хотите приобрести (Баланс: {balance[1]}ST ({hu_number(balance[1])})', reply_markup=None)
    if call.data == 'agree_buy_box':
        data = await state.get_data()
        text = buy_boxes(user_id, username, data['pcs'])
        await bot.answer_callback_query(call.id)
        await call.message.edit_text(text, reply_markup=None)
        await state.clear()

    if call.data == 'cancel':
        await call.message.edit_text('✅ Транзакция отменена', reply_markup=None)

@router.message(Buy_V.pcs)
async def buy_v(message: Message, state: FSMContext):
    await advanced_buy('V', state, message, inline)

@router.message(Sell_V.pcs)
async def sell_v(message: Message, state: FSMContext):
    await advanced_sell('V', state, message, inline)

@router.message(Buy_ST.pcs)
async def buy_st(message: Message, state: FSMContext):
    await advanced_buy('ST', state, message, inline)

@router.message(Sell_ST.pcs)
async def sell_st(message: Message, state: FSMContext):
    await advanced_sell('ST', state, message, inline)

@router.message(Buy_Boxes.pcs)
async def buy_box(message: Message, state: FSMContext):
    await advanced_buy_boxes('Box', state, message, inline)

