from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from utils.states import Buy_V, Sell_V, Buy_ST, Sell_ST

from data.datebase import get_price, get_profile, buy_coins, sell_coins, advanced_buy, advanced_sell

from keyboards import inline

router = Router()

@router.callback_query()
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username

    if call.data == 'buy':
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.from_user.id, 'Выберите валюту', reply_markup=inline.buy_buttons)
    if call.data == 'sell':
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.from_user.id, 'Выберите валюту', reply_markup=inline.sell_buttons)

    if call.data == 'buy_v':
        await state.set_state(Buy_V.pcs)
        await call.message.edit_text('Введите количество V, которое вы хотите приобрести')
        await bot.answer_callback_query(call.id)
    if call.data == 'sell_v':
        await state.set_state(Sell_V.pcs)
        await call.message.edit_text('Введите количество V, которое вы хотите продать')
        await bot.answer_callback_query(call.id)

    if call.data == 'edit_buy_v':
        await state.set_state(Buy_V.pcs)
        await call.message.edit_text('Введите количество V, которое вы хотите приобрести', reply_markup=None)
        await bot.answer_callback_query(call.id)
    if call.data == 'edit_sell_v':
        await state.set_state(Sell_V.pcs)
        await call.message.edit_text('Введите количество V, которое вы хотите продать', reply_markup=None)
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
        await call.message.edit_text('Введите количество ST, которое вы хотите приобрести')
        await bot.answer_callback_query(call.id)
    if call.data == 'sell_st':
        await state.set_state(Sell_ST.pcs)
        await call.message.edit_text('Введите количество ST, которое вы хотите продать')
        await bot.answer_callback_query(call.id)

    if call.data == 'edit_buy_st':
        await state.set_state(Buy_ST.pcs)
        await bot.answer_callback_query(call.id)
        await call.message.edit_text('Введите количество ST, которое вы хотите приобрести', reply_markup=None)
    if call.data == 'edit_sell_st':
        await state.set_state(Sell_ST.pcs)
        await bot.answer_callback_query(call.id)
        await call.message.edit_text('Введите количество ST, которое вы хотите продать', reply_markup=None)
    
    if call.data == 'agree_buy_st':
        data = await state.get_data()

        text = buy_coins(user_id, username, 'ST', data['pcs'])

        await call.message.edit_text(text, reply_markup=None)

        await state.clear()

    if call.data == 'agree_sell_st':
        data = await state.get_data()

        text = sell_coins(user_id, username, 'ST', data['pcs'])

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

