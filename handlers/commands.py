from aiogram import Router
from aiogram.filters import Command, CommandStart
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

    await message.answer(
        f"Привет, <b>{message.from_user.first_name}</b>!\nТы попал в бот <b>ST Bank</b> (v{version})\n\nЗдесь тебе придётся торговать акциями, открывать боксы, фиксировать <s>убытки</s> прибыль",
        reply_markup=keyboard,
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    text = (
        "🏦 <b>ST Bank - Виртуальная торговля</b>\n\n"
        "<b>Что это?</b>\n"
        "Бот для торговли виртуальными валютами и коллекционирования предметов.\n\n"
        "<b>💰 Валюты:</b>\n"
        "• <b>ST</b> - стабильная валюта (для новичков)\n"
        "• <b>V</b> - рискованная валюта (может сильно расти или падать)\n"
        "• <b>RUB</b> - рубли для покупок\n\n"
        "<b>📦 Боксы:</b>\n"
        "Открывайте их и получайте редкие предметы!\n\n"
        "<b>🎯 Как начать:</b>\n"
        '1. Нажмите "💲 Открыть брокерский счёт"\n'
        "2. Получите стартовый капитал\n"
        "3. Покупайте валюты по низкой цене\n"
        "4. Продавайте по высокой цене\n"
        "5. Получайте прибыль!\n\n"
        "<b>📊 Полезные функции:</b>\n"
        "• Профиль - посмотреть баланс\n"
        "• Торговать - купить/продать валюты\n"
        "• Статистика - анализ прибыли\n"
        "• Уведомления - включить в профиле\n\n"
        "<b>⚠️ Важно:</b>\n"
        "• Все валюты виртуальные\n"
        "• Цены меняются каждые 2-5 минут\n"
        "• Можно как заработать, так и потерять\n\n"
        "<b>🔧 Команды:</b>\n"
        "• /chance - шанс роста ST\n"
        "• /help - эта помощь\n"
        "• /start - начать заново\n\n"
        "<i>Разработчик: @zenqst</i>"
    )
    await message.answer(text)


@router.message(Command("chance"))
async def chance_handler(message: Message):
    percent = await calculate_precise_growth_chance("st")
    await message.answer(f"Шанс повышения ST: {percent}")
