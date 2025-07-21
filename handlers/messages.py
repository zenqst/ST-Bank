from aiogram import Router, F
from aiogram.types import Message
import prettytable as pt

from keyboards.reply import main
from keyboards.inline import profile_buttons, action_buttons

from database.queries import get_profile, register, get_price

from states.enums import UserStatus

from config_reader import config, v


router = Router()

@router.message(F.text.lower().in_(["💲 открыть брокерский счёт"]))
async def start_message(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    status = await register(user_id, username)

    if status == UserStatus.SUCCESS:
        await message.reply("✅ <b>Поздравляю! Вы открыли брокерский счёт в ST Bank.</b>\n\nВ подарок вам было выдано <b>5000₽, 15ST, 3V и 3 📦</b>\n\n⚠️ Акции не являются настоящими. Все валюты исключительно виртуальные и не связаны с реальными денежными средствами.", reply_markup = main)
    elif status == UserStatus.ALREADY_EXISTS:
        await message.reply("❌ <b>Вы уже были зарегистрированы ранее!</b>")
    else:
        await message.reply("⛔️ <b>Возникла неизвестная ошибка!</b>")


async def send_table(data):
    table = pt.PrettyTable(['Название', 'Количество', 'Стоимость'])
    table.align['Название'] = 'l'
    table.align['Количество'] = 'r'
    table.align['Стоимость'] = 'r'

    for symbol, price, cost in data:
        table.add_row([symbol, f'{price:.2f}', cost])

    return table

@router.message(F.text.lower().in_(["📋 профиль"]))
async def profile(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    data = await get_profile(user_id)
    st_price = await get_price("st")
    v_price = await get_price("v")
    
    table = await send_table([
        ('RUB', data['rubles'], '—'),
        ('ST', data['st'], f'~{st_price['cost'] * data['st']} RUB'),
        ('V', data['v'], f'~{v_price['cost'] * data['v']} RUB'),
        ('BOX', data['boxes'], '—')
    ])
    
    await message.answer(f"<b>📋 Профиль пользователя @{username}</b> (<i>{user_id}</i>)\n\n<pre>{table}</pre>", reply_markup=profile_buttons)

@router.message(F.text.lower().in_(["📊 торговать"]))
async def trade(message: Message):
    st_price = await get_price("st")
    v_price = await get_price("v")

    await message.answer(f"<b>Текущие цены:</b>\n1 ST = {st_price['cost']} RUB <i>({st_price['diff']})</i>\n1 V = {v_price['cost']} RUB <i>({v_price['diff']})</i>", reply_markup=action_buttons)
