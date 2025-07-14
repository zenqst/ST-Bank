from aiogram import Router, Bot
from aiogram.types import Message, LabeledPrice
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext

from os import _exit as exit
import asyncio
from logging import error
from asyncio import sleep

from config_reader import config
from database.queries import check_profile, check_casino_balance
from database.core import db
from states.enums import UserStatus
from states.fsm_states import Interaction
from keyboards.reply import register, main

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    status = await check_profile(user_id)

    if status == UserStatus.NOT_FOUND:
        keyboard = register
    else:
        keyboard = main

    await message.answer(f"Привет, <b>{message.from_user.first_name}</b>!\nТы попал в бот <b>ST Bank</b> ({config.version[0]})\n\nЗдесь тебе придётся торговать акциями, открывать боксы, фиксировать <s>убытки</s> прибыль", reply_markup = keyboard)

@router.message(Command("check"))
async def check(message: Message, state: FSMContext):
    status = await check_profile(message.from_user.id)
    data = await state.get_data()

    await message.answer(f"Текущий статус: {status}\n\nДанные Interaction: {data}")

@router.message(Command("game"))
async def handler_game(message: Message): 
    user_id = message.from_user.id

    msg = await message.answer_dice(emoji="🎰")
    value = msg.dice.value
    balance = await check_casino_balance(user_id)

    balance_now = balance['casino_pts'] + value - 30
    await db.update_data("users", {"casino_pts": balance_now}, {"id": user_id})

    res_msg = await msg.reply(f"⏳ <b>Обработка результата...</b>")
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
    exit(0)