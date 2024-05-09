from aiogram import Router, F
from aiogram.types import Message

from keyboards import reply, inline, builders, fabrics

from config_reader import config

from data.datebase import get_profile, get_price

router = Router()

current_page = 1
total_pages = 2

@router.message(F.text.lower().in_(["💲 открыть брокерский счёт"]))
async def open(message: Message):
    await message.reply("✅ <b>Поздравляю! Вы открыли брокерский счёт в ST Bank.</b>\n\nВ подарок вам было выдано <b>2000₽, 10ST и 5V</b>\n\n⚠️ Акции не являются настоящими. Все валюты исключительно виртуальные и не связаны с реальными денежными средствами.", reply_markup = reply.main)

@router.message(F.text.lower().in_(["🔙 вернуться"]))
async def back(message: Message):
    await message.answer(f"Привет, <b>{message.from_user.first_name}</b>!\nТы попал(-а) в бот <b>ST Seller</b> ({config.version}).\n\n⚠️ Пока что бот находится в закрытом альфа-тестировании, для получения доступа обратитесь к @zenq_st", reply_markup=reply.main)

@router.message(F.text.lower().in_(["📋 профиль"]))
async def profile(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    data = get_profile(user_id, username)

    if data:
        await message.answer(f'📋 Профиль пользователя @{username}\n\n<b>ID:</b> {user_id}\n<b>Рубли:</b> {data[0]}\n<b>ST:</b> {data[1]}\n<b>V:</b> {data[2]}', reply_markup=inline.profile_buttons)
    else:
        await message.answer('⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.')

@router.message(F.text.lower().in_(["📊 торговать"]))
async def torg(message: Message):
    data_st = get_price('ST')
    data_v = get_price('V')

    if float(data_st[1]) >= 0:
        percent_st = f'+{data_st[1]}%'
    else:
        percent_st = f'{data_st[1]}%'

    if float(data_v[1]) >= 0:
        percent_v = f'+{data_v[1]}%'
    else:
        percent_v = f'{data_v[1]}%'

    await message.answer(f'<b>Текущая цена:</b>\n1ST = {data_st[0]}₽ ({percent_st})\n1V = {data_v[0]}₽ ({percent_v})', reply_markup=inline.st_buttons)

# @router.message()
# async def echo(message: Message):
#     await message.reply("Я вас не понимаю...")