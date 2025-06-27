from aiogram import Router, F
from aiogram.types import Message

from keyboards import reply, inline, builders, fabrics

from data.queries import get_profile, get_price, register

from utils.enums import UserStatus

from config_reader import config, v


router = Router()

@router.message(F.text.lower().in_(["💲 открыть брокерский счёт"]))
async def open(message: Message):
    status = await register(message.from_user.id, message.from_user.username)

    if status == UserStatus.SUCCESS:
        await message.reply("✅ <b>Поздравляю! Вы открыли брокерский счёт в ST Bank.</b>\n\nВ подарок вам было выдано <b>2000₽, 10ST и 5V</b>\n\n⚠️ Акции не являются настоящими. Все валюты исключительно виртуальные и не связаны с реальными денежными средствами.", reply_markup = reply.main)
    elif status == UserStatus.ALREADY_EXISTS:
        await message.reply("❌ <b>Вы уже были зарегистрированы ранее!</b>")
    else:
        await message.reply("⛔️ <b>Возникла неизвестная ошибка!</b>")

@router.message(F.text.lower().in_(["🔙 вернуться"]))
async def back(message: Message):
    await message.answer(f"Привет, <b>{message.from_user.first_name}</b>!\nТы попал(-а) в бот <b>ST Seller</b> ({config.version}).\n\n⚠️ Пока что бот находится в закрытом альфа-тестировании, для получения доступа обратитесь к @zenq_st", reply_markup=reply.main)

@router.message(F.text.lower().in_(["📋 профиль"]))
async def profile(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    data = await get_profile(user_id, username)

    if data:
        await message.answer(f'📋 Профиль пользователя @{username}\n\n<b>ID:</b> {user_id}\n<b>Рубли:</b> {data[0]}\n<b>ST:</b> {data[1]}\n<b>V:</b> {data[2]}\n📦: {data[3]}', reply_markup=inline.profile_buttons)
    else:
        await message.answer('⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.')

@router.message(F.text.lower().in_(["📦 открыть бокс"]))
async def open_box_func(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    data = await get_profile(user_id, username)

    await message.answer(f'Текущее кол-во Боксов: <b>{data[3]} 📦</b>\n\nВыберите действие:', reply_markup=inline.box_buttons)

@router.message(F.text.lower().in_(["📊 торговать"]))
async def torg(message: Message):
    data_st = await get_price('st')
    data_v = await get_price('v')

    if float(data_st[1]) >= 0:
        percent_st = f'+{data_st[1]}%'
    else:
        percent_st = f'{data_st[1]}%'

    if float(data_v[1]) >= 0:
        percent_v = f'+{data_v[1]}%'
    else:
        percent_v = f'{data_v[1]}%'

    await message.answer(f'<b>Текущие цены:</b>\n1ST = {data_st[0]}₽ <i>({percent_st})</i>\n1V = {data_v[0]}₽ <i>({percent_v})</i>', reply_markup=inline.choose_type_buttons)

@router.message(F.text.lower().in_(["🆕 донаты"]))
async def donates(message: Message):
    await message.answer(f'☹️ Провалились акции? Не хватает ST на открытие боксов?\n😇 ST Bank предлагает <b>новое решение!</b> Преобразуйте свои рубли в валюту\n\n<b>{v.in_irl_rub} IRL RUB = 1V</b>\n\n', reply_markup=inline.donate_buttons)

# @router.message()
# async def echo(message: Message):
#     await message.reply("Я вас не понимаю...")