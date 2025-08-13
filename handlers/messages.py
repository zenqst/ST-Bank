
from aiogram import F, Router
from aiogram.types import Message

from asyncio import sleep
from random import uniform
from database.core import db
from database.messages import send_admin_panel_message, send_prices_msg, send_profile
from database.user import check_casino_balance, get_profile, register
from keyboards.builders import create_box_button, create_main_buttons
from states.enums import UserStatus

router = Router()


@router.message(F.text.lower().in_(["💲 открыть брокерский счёт"]))
async def start_message(message: Message):
    if message.from_user is None:
        return

    user_id = message.from_user.id
    username = message.from_user.username

    status = await register(user_id, username)
    main_kb = await create_main_buttons(user_id)

    if status == UserStatus.SUCCESS:
        await message.reply("✅ <b>Поздравляю! Вы открыли брокерский счёт в ST Bank.</b>\n\nВ подарок вам было выдано <b>5000₽, 15ST, 3V и 3 📦</b>\n\n⚠️ Акции не являются настоящими. Все валюты исключительно виртуальные и не связаны с реальными денежными средствами.", reply_markup=main_kb)
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


@router.message(F.text.lower().in_(["🎛 админ-панель"]))
async def admin_panel(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    await send_admin_panel_message(user_id, username, message)


@router.message(F.text.lower().in_(["🎰 игра [β]"]))
async def game(message: Message):
    user_id = message.from_user.id

    msg = await message.answer_dice(emoji="🎰")
    value = msg.dice.value
    balance = await check_casino_balance(user_id)
    result = value - 30

    balance_now = balance['casino_pts'] + result
    await db.update_data("users", {"casino_pts": balance_now}, {"id": user_id})

    res_msg = await msg.reply("⏳ <b>Обработка результата...</b>")
    await sleep(2.5)

    await res_msg.edit_text(f"<b>Ваш результат: {value}</b>\n\nТекущий баланс: {balance_now} <i>[{'+' if result > 0 else ''}{result}]</i>")