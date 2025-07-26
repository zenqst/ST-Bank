import asyncio
import sys
import tomllib
from asyncio import sleep
from logging import error
from random import uniform

from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.text_decorations import html_decoration

from config_reader import config
from database.core import db
from database.queries import (
    calculate_precise_growth_chance,
    change_coin,
    check_casino_balance,
    check_profile,
    send_broadcast_message,
)
from keyboards.reply import main, register
from states.enums import UserStatus
from states.fsm_states import BroadcastText

router = Router()


async def get_version_from_pyproject() -> str:
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


@router.message(CommandStart())
async def start(message: Message):
    if message.from_user is None:
        return

    user_id = message.from_user.id
    status = await check_profile(user_id)
    
    keyboard = register if status == UserStatus.NOT_FOUND else main

    version = await get_version_from_pyproject()

    await message.answer(f"Привет, <b>{message.from_user.first_name}</b>!\nТы попал в бот <b>ST Bank</b> (v{version})\n\nЗдесь тебе придётся торговать акциями, открывать боксы, фиксировать <s>убытки</s> прибыль", reply_markup=keyboard)


@router.message(Command("check"))
async def check_handler(message: Message, state: FSMContext):
    status = await check_profile(message.from_user.id)
    data = await state.get_data()
    random_nu = uniform(2.50, 5.00)

    await message.answer(f"Текущий статус: {status}\n\nДанные Interaction: {data}\n\nRandom: {random_nu}", parse_mode=None)
    

@router.message(Command("change"))
async def change_handler(message: Message, bot: Bot):
    await change_coin("st", bot)
    await message.answer("Валюта ST изменена")


@router.message(Command("chance"))
async def chance_handler(message: Message):
    percent = await calculate_precise_growth_chance("st")
    await message.answer(f"Шанс повышения ST: {percent}")


@router.message(Command("users"))
async def users_handler(message: Message):
    text = ""

    users = await db.select_data("users", "*", fetch_all=True)

    for i, user in enumerate(users):
        username = user.get("username")
        user_id = user.get("id")
        text += f"{i + 1}. @{username} ({user_id})\n"
    
    text += f"\nОбщее кол-во пользователей: {len(users)}"
    await message.answer(text)


@router.message(Command("send"))
async def send_text_handler(message: Message, state: FSMContext):
    await message.answer("<b>📝 В следующем сообщении отправьте текст для рассылки</b>")
    await state.set_state(BroadcastText.sending_text)


@router.message(BroadcastText.sending_text)
async def interaction_amount_handler(message: Message, state: FSMContext, bot: Bot):
    if message.text:
        formatted_text = message.text
    elif message.caption:
        formatted_text = message.caption
    else:
        await message.answer("❌ Пожалуйста, отправьте текст для рассылки")
        return
    
    # Если есть entities, конвертируем их в HTML
    if message.text and message.entities:
        formatted_text = html_decoration.unparse(message.text, message.entities)
    elif message.caption and message.caption_entities:
        formatted_text = html_decoration.unparse(message.caption, message.caption_entities)
    
    await state.update_data(sending_text=formatted_text)
    await send_broadcast_message(state, bot)


@router.message(Command("game"))
async def handler_game(message: Message): 
    user_id = message.from_user.id

    msg = await message.answer_dice(emoji="🎰")
    value = msg.dice.value
    balance = await check_casino_balance(user_id)

    balance_now = balance['casino_pts'] + value - 30
    await db.update_data("users", {"casino_pts": balance_now}, {"id": user_id})

    res_msg = await msg.reply("⏳ <b>Обработка результата...</b>")
    await sleep(3)

    await res_msg.edit_text(f"<b>Ваш результат: {value}</b>\n\nТекущий баланс: {balance_now}")


@router.message(Command("shut"))
async def shutdown_handler(message: Message):
    if message.from_user.id != config.admin_id:
        pass

    await message.answer("Бот выключается...")

    asyncio.create_task(shutdown())


async def shutdown():   
    error("Bot shutdowned by command")
    sys.exit(0)