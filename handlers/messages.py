from aiogram import F, Router
from aiogram.types import Message

from database.queries import get_profile, register, send_prices_msg, send_profile
from keyboards.builders import create_box_button
from keyboards.reply import main
from states.enums import UserStatus

router = Router()


@router.message(F.text.lower().in_(["💲 открыть брокерский счёт"]))
async def start_message(message: Message):
    if message.from_user is None:
        return

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
    if message.from_user is None:
        return

    await send_profile(message.from_user.id, message.from_user.username, message)


@router.message(F.text.lower().in_(["📊 торговать"]))
async def trade(message: Message):
    await send_prices_msg(message)


@router.message(F.text.lower().in_(["📦 открыть бокс"]))
async def boxes(message: Message):
    if message.from_user is None:
        return
    
    profile = await get_profile(message.from_user.id)

    inline_kb = await create_box_button(amount=None, box_balance=profile['box'])

    text = (
        "Меню взаимодействия с Боксами\n\n"
        "<b>Краткая сводка:</b>\n"
        "Открытие Боксов — процесс, при котором вы тратите свои BOX, а взамен получаете предметы разных редкостей. Можно выбрать количество Боксов для открытия — от 1 до 10. Существует 10% шанс на то, что Бокс будет сохранён.\n"
        "Покупка Боксов — обычная покупка валюты BOX, но при этом цена всегда статична (может меняться лишь только при обновлениях).\n\n"
        f"<b>Баланс BOX:</b> {profile['box']} BOX\n\n"
        "<i>Помните, что все предметы вымышлены, совпадения случайны.</i>"
    )

    await message.answer(text, reply_markup=inline_kb)
    