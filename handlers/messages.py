from aiogram import Router, F
from aiogram.types import Message
import prettytable as pt

from keyboards.reply import main

from database.queries import get_profile, register

from states.enums import UserStatus

from config_reader import config, v


router = Router()

@router.message(F.text.lower().in_(["💲 открыть брокерский счёт"]))
async def open(message: Message):
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
    table = pt.PrettyTable(['Название', 'Количество'])
    table.align['Название'] = 'l'
    table.align['Количество'] = 'r'

    for symbol, price in data:
        table.add_row([symbol, f'{price:.2f}'])

    return table

@router.message(F.text.lower().in_(["📋 профиль"]))
async def open(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    data = await get_profile(user_id)
    
    table = await send_table([
        ('RUB', data['rubles']),
        ('ST', data['st']),
        ('V', data['v']),
        ('BOX', data['boxes'])
    ])
    
    # profile_msg = (
    #     f"<b>📋 Профиль пользователя @{username}</b> (<i>{user_id}</i>)\n\n"
    #     f"<b>RUB:</b> {data['rubles']}\n"
    #     f"<b>ST:</b> {data['st']}\n"
    #     f"<b>V:</b> {data['v']}\n"
    #     f"<b>📦:</b> {data['boxes']}\n"
    # )
    
    await message.reply(f"<b>📋 Профиль пользователя @{username}</b> (<i>{user_id}</i>)\n\n<pre>{table}</pre>")