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
    
    <i>Добро пожаловать в мир виртуальной экономики и трейдинга!</i>

    <b>📋 Основные функции платформы:</b>

    💰 <b>Торговая система</b>
    • <b>ST (Stable Token)</b> - стабильная валюта с умеренной волатильностью, идеальна для начинающих трейдеров
    • <b>V (Volatile Token)</b> - высокорискованная валюта с экстремальными колебаниями цен
    • Динамическое ценообразование с автоматическими обновлениями
    • Система трендов и технического анализа

    📦 <b>Система лутбоксов</b>
    • Коллекционные предметы различной редкости
    • Система компенсаций за дубликаты
    • Возможность отслеживания коллекции

    📊 <b>Аналитика и статистика</b>
    • Детальная статистика торговых операций
    • Расчёт ROI (Return on Investment) по каждой валюте
    • История сделок и анализ прибыльности
    • Отслеживание лучших сделок

    🎰 <b>Игровые функции</b>
    • Казино с игровыми поинтами (бета-версия)

    <b>🎯 Пошаговое руководство:</b>
    1. <b>Регистрация:</b> Нажмите "💲 Открыть брокерский счёт"
    2. <b>Стартовый капитал:</b> Получите 5,000₽, 15 ST, 3 V и 3 лутбокса
    3. <b>Изучение рынка:</b> Анализируйте цены в разделе "📊 Торговать"
    4. <b>Первые сделки:</b> Начните с покупки ST при низких ценах
    5. <b>Развитие:</b> Постепенно переходите к торговле V
    6. <b>Диверсификация:</b> Открывайте боксы для получения предметов

    <b>⚠️ Важная информация:</b>
    • Все валюты и предметы являются виртуальными активами
    • Цены обновляются автоматически каждые 2.5-5 минут
    • Система использует алгоритмы случайного ценообразования
    • Возможны как значительные прибыли, так и убытки

    <b>💡 Профессиональные советы:</b>
    • Изучайте графики и тренды перед совершением сделок
    • Не инвестируйте все средства в одну валюту
    • Используйте функцию "Статистика" для анализа эффективности
    • Следите за уведомлениями о резких изменениях цен

    <b>🔧 Дополнительные команды:</b>
    • <code>/chance</code> - показать вероятность роста ST
    • Уведомления о важных изменениях цен
    • Возможность сброса аккаунта через банкротство

    <i>Удачной торговли и высоких прибылей! 📈</i>
    
    <i>Разработчик: @zenqst</i>
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