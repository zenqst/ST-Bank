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


@router.message(Command("help"))
async def help_handler(message: Message):
    help_text = """
    🏦 <b>ST Bank - Виртуальная торговая платформа</b>

    <b>📋 Основные функции:</b>

    💰 <b>Торговля</b> - Покупайте и продавайте виртуальные валюты:
    • <b>ST</b> - стабильная валюта для новичков
    • <b>V</b> - волатильная валюта с высокими рисками

    📦 <b>Боксы</b> - Открывайте лутбоксы и собирайте предметы разной редкости

    📊 <b>Профиль</b> - Просматривайте баланс, статистику и портфель

    🎰 <b>Игра</b> - Испытайте удачу в слот-машине (бета)

    <b>🎯 Как начать:</b>
    1. Нажмите "💲 Открыть брокерский счёт" для регистрации
    2. Получите стартовый капитал: 5000₽, 15 ST, 3 V, 3 BOX
    3. Изучайте цены в разделе "📊 Торговать"
    4. Покупайте дешево, продавайте дорого!

    <b>⚠️ Важно:</b>
    • Все валюты виртуальные и не имеют реальной стоимости
    • Цены обновляются каждые 2.5-5 минут
    • Следите за трендами для успешной торговли

    <b>💡 Совет:</b> Начните с торговли ST, затем переходите к более рискованной V

    Удачной торговли! 📈
    """
    await message.answer(help_text)


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