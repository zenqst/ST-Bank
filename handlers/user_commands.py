from aiogram import Router, Bot
from aiogram.types import Message, LabeledPrice
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext

from keyboards import reply
from keyboards import builders

from config_reader import config

from data.queries import get_profile, sending

from utils.states import Sending_Text
from utils.enums import UserStatus

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id

    status = await get_profile(user_id)

    if status == UserStatus.NOT_FOUND:
        reply_markup = reply.register
    else:
        reply_markup = reply.main
    
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