from aiogram import Router, Bot
from aiogram.types import Message, LabeledPrice
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext

import asyncio

from config_reader import config

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    # TODO: Доделать тут нормально
    await message.answer(f"LOREM IPSUM MUHAHA")

@router.message(Command("shut"))
async def shutdown_handler(message: Message):
    if message.from_user.id != config.admin_id:
        pass

    await message.answer("Бот выключается...")

    asyncio.create_task(shutdown())

async def shutdown():
    await asyncio.sleep(1)
    import os
    os._exit(0)