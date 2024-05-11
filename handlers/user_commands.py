from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject, CommandStart

from keyboards import reply

from config_reader import config

from data.datebase import register, get_profile

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    if register(user_id, username):
        reply_markup = reply.main
    else:
        reply_markup = reply.register
    
    await message.answer(f"Привет, <b>{message.from_user.first_name}</b>!\nТы попал(-а) в бот <b>ST Bank</b> ({config.version[0]})", reply_markup=reply_markup)