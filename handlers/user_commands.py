from aiogram import Router, Bot
from aiogram.types import Message, LabeledPrice
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext

from keyboards import reply
from keyboards import builders

from config_reader import config

from data.datebase import register, sending

from utils.states import Sending_Text

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    if await register(user_id, username):
        reply_markup = reply.main
    else:
        reply_markup = reply.register
    
    await message.answer(f"Привет, <b>{message.from_user.first_name}</b>!\nТы попал(-а) в бот <b>ST Bank</b> ({config.version[0]})\n\nЗдесь тебе придётся торговать акциями, открывать боксы, <i>фиксировать убытики</i>", reply_markup=reply_markup)

@router.message(Command('sending'))
async def sending_command(message: Message, state: FSMContext):
    if message.from_user.id == config.admin_id:
        await state.set_state(Sending_Text.text)
        await message.answer('Отправьте текст рассылки')

@router.message(Sending_Text.text)
async def sending_process(message: Message, state: FSMContext):
    data = await state.get_data()
    result = await sending(data['text'], Bot)

    await message.reply(result)

    await state.clear()