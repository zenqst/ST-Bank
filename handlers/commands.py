from aiogram import Router, Bot
from aiogram.types import Message, LabeledPrice
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext

from os import _exit as exit
import asyncio
from logging import error

from config_reader import config
from database.queries import check_profile

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    # TODO: Доделать тут нормально
    await message.answer(f"LOREM IPSUM MUHAHA")

@router.message(Command("check"))
async def check(message: Message):
    status = await check_profile(message.from_user.id)
    await message.answer(status)

@router.message(Command("shut"))
async def shutdown_handler(message: Message):
    if message.from_user.id != config.admin_id:
        pass

    await message.answer("Бот выключается...")

    asyncio.create_task(shutdown())

async def shutdown():
    await asyncio.sleep(1)
    error("Bot shutdowned by command")
    exit(0)