from aiogram import F, Router
from aiogram.types import Message

from database.queries import get_price, get_profile, register, send_profile
from keyboards.inline import action_buttons, box_buttons
from keyboards.reply import main
from states.enums import UserStatus

router = Router()


@router.message(F.text.lower().in_(["💲 открыть брокерский счёт"]))
async def start_message(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    status = await register(user_id, username)

    if status == UserStatus.SUCCESS:
        await message.reply("✅ <b>Поздравляю! Вы открыли брокерский счёт в ST Bank.</b>\n\nВ подарок вам было выдано <b>5000₽, 15ST, 3V и 3 📦</b>\n\n⚠️ Акции не являются настоящими. Все валюты исключительно виртуальные и не связаны с реальными денежными средствами.", reply_markup=main)
    elif status == UserStatus.ALREADY_EXISTS:
        await message.reply("❌ <b>Вы уже были зарегистрированы ранее!</b>")
    else:
        await message.reply("⛔️ <b>Возникла неизвестная ошибка!</b>")


@router.message(F.text.lower().in_(["📋 профиль"]))
async def profile(message: Message):
    await send_profile(message.from_user.id, message.from_user.username, message)


@router.message(F.text.lower().in_(["📊 торговать"]))
async def trade(message: Message):
    st_price = await get_price("st")
    v_price = await get_price("v")

    await message.answer(f"<b>Текущие цены:</b>\n1 ST = {st_price['cost']} RUB <i>({st_price['diff']})</i>\n1 V = {v_price['cost']} RUB <i>({v_price['diff']})</i>", reply_markup=action_buttons)


@router.message(F.text.lower().in_(["📦 открыть бокс"]))
async def boxes(message: Message):
    profile = await get_profile(message.from_user.id)

    await message.answer(f"Меню взаимодействия с Боксами\n\n<b>Краткая сводка:</b>\nОткрытие Боксов — процесс, при котором вы тратите свои BOX, а взамен получаете предметы разных редкостей. Можно выбрать количество Боксов для открытия — от 1 до 10. Существует 10% шанс на то, что Бокс будет сохранён.\nПокупка Боксов — обычная покупка валюты BOX, но при этом цена всегда статична (может меняться лишь только при обновлениях).\n\n<b>Баланс BOX:</b> {profile['box']} BOX\n\n<i>Помните, что все предметы вымышлены, совпадения случайны.</i>", reply_markup=box_buttons)
