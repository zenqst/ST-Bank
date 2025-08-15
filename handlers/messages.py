from asyncio import sleep

from aiogram import F, Router
from aiogram.types import Message

from database.core import db
from database.currencies import edit_boxes_handler
from database.messages import send_admin_panel_message, send_prices_msg, send_profile
from database.user import check_casino_balance, register
from keyboards.builders import create_main_buttons
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
        await message.reply(
            "✅ <b>Поздравляю! Вы открыли брокерский счёт в ST Bank.</b>\n\nВ подарок вам было выдано <b>5000₽, 15ST, 3V и 3 📦</b>\n\n⚠️ Акции не являются настоящими. Все валюты исключительно виртуальные и не связаны с реальными денежными средствами.",
            reply_markup=main_kb,
        )
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

    await edit_boxes_handler(message)


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

    balance_now = balance["casino_pts"] + result
    await db.update_data("users", {"casino_pts": balance_now}, {"id": user_id})

    res_msg = await msg.reply("⏳ <b>Обработка результата...</b>")
    await sleep(2.5)

    await res_msg.edit_text(
        f"<b>Ваш результат: {value}</b>\n\nТекущий баланс: {balance_now} <i>[{'+' if result > 0 else ''}{result}]</i>\n\n<i>В одном из следующих обновлений все поинты будут автоматически переведены в RUB</i>"
    )
