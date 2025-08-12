import asyncio
import sys
import tomllib
from asyncio import sleep
from logging import error
from random import uniform

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config_reader import config
from database.core import db
from database.currencies import calculate_precise_growth_chance
from database.user import check_casino_balance, check_profile
from keyboards.builders import create_main_buttons
from keyboards.reply import register
from states.enums import UserStatus

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
    main_kb = await create_main_buttons(user_id)

    keyboard = register if status == UserStatus.NOT_FOUND else main_kb

    version = await get_version_from_pyproject()

    await message.answer(f"Привет, <b>{message.from_user.first_name}</b>!\nТы попал в бот <b>ST Bank</b> (v{version})\n\nЗдесь тебе придётся торговать акциями, открывать боксы, фиксировать <s>убытки</s> прибыль", reply_markup=keyboard)


@router.message(Command("check"))
async def check_handler(message: Message, state: FSMContext):
    status = await check_profile(message.from_user.id)
    data = await state.get_data()
    random_nu = uniform(2.50, 5.00)

    await message.answer(f"Текущий статус: {status}\n\nДанные Interaction: {data}\n\nRandom: {random_nu}", parse_mode=None)


@router.message(Command("chance"))
async def chance_handler(message: Message):
    percent = await calculate_precise_growth_chance("st")
    await message.answer(f"Шанс повышения ST: {percent}")


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
    if message.from_user.id not in config.admin_ids:
        pass

    await message.answer("Бот выключается...")

    asyncio.create_task(shutdown())


async def shutdown():   
    error("Bot shutdowned by command")
    sys.exit(0)