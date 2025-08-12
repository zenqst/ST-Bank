from random import uniform

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.currencies import calculate_precise_growth_chance
from database.user import check_profile
from keyboards.builders import create_main_buttons
from keyboards.reply import register
from states.enums import UserStatus
from utils.control import get_version_from_pyproject

router = Router()


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