import asyncio
import datetime as dt
import logging
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from asyncpg.exceptions import PostgresError

from config_reader import config
from database.core import db
from database.currencies import get_price
from database.user import get_profile
from database.utils import format_number, send_table
from keyboards.builders import create_profile_buttons
from keyboards.inline import action_buttons, admin_buttons, admins_return_buttons
from states.types import TableProfile

logger = logging.getLogger(__name__)


async def send_prices_msg(message: Message | CallbackQuery) -> None:
    """
    Функция, которая отправляет текущие цены

    :param message: Message or CallbackQuery
    :return: None
    """
    st_price = await get_price("st")
    v_price = await get_price("v")

    text = (
        "<b>Текущие цены:</b>\n"
        f"1 ST = {st_price['cost']} RUB <i>({st_price['diff']})</i>\n"
        f"1 V = {v_price['cost']} RUB <i>({v_price['diff']})</i>"
    )

    if isinstance(message, Message):
        await message.answer(text, reply_markup=action_buttons)
    elif isinstance(message, CallbackQuery):
        if message.message is not None and isinstance(message.message, Message):
            await message.message.edit_text(text, reply_markup=action_buttons)
            await message.answer()
        else:
            await message.answer(text, reply_markup=action_buttons)


async def send_for_admins(bot: Bot, text: str) -> None:
    for adm_id in config.admin_ids:
        await send_single_message(bot, adm_id, text)


async def send_single_message(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(user_id, text)
        await asyncio.sleep(0.05)
    except TelegramAPIError as e:
        logger.warning("Не удалось отправить сообщение пользователю %d: %s", user_id, e)
        raise


async def send_broadcast_message(
    sending_text: FSMContext | str, bot: Bot, author_id: int | None = None
) -> None:
    try:
        all_users: list[dict[str, Any]] = await db.select_data("users", "*", fetch_all=True)
    except PostgresError:
        logger.exception("Ошибка при получении списка пользователей: %s")
        return

    if not all_users:
        return

    successful = 0
    failed = 0
    tasks = []
    if isinstance(sending_text, str):
        text = sending_text
    else:
        data = await sending_text.get_data()
        text = data.get("sending_text")

    for user in all_users:
        user_id = user.get("id")
        if not user_id:
            logger.warning("Пропущен пользователь без ID: %s", user)
            failed += 1
            continue

        if isinstance(sending_text, str) and not user.get("notify"):
            continue
        task = asyncio.create_task(send_single_message(bot, user_id, text))
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.error("Ошибка при отправке сообщения: %s", result)
            failed += 1
        else:
            successful += 1

    if isinstance(sending_text, FSMContext) and author_id:
        try:
            await bot.send_message(
                author_id,
                f"Рассылка завершена!\n\n✅ Успешно: {successful}\n❌ Не отправлено: {failed}",
            )
        except TelegramAPIError:
            logger.exception("Не удалось отправить отчёт админу: %s")

        await sending_text.clear()


async def send_profile(
    user_id: int, username: str | None, message: Message | CallbackQuery, is_admin: bool = False
) -> None:
    """
    Функция для отправки сообщения с профилем

    :param user_id: Айди юзера
    :param username: Никнейм юзера
    :param message: Message или CallbackQuery (зависит от расположения функции)
    :return: None
    """

    data: TableProfile = await get_profile(user_id)

    st_price = await get_price("st")
    v_price = await get_price("v")
    st_value: float = st_price.get("cost") * data.get("st")
    v_value: float = v_price.get("cost") * data.get("v")

    total_value = data.get("rubles") + st_value + v_value
    total_formatted_value = await format_number(total_value)

    data_for_table: TableProfile = [
        ("RUB", data.get("rubles"), "—"),
        ("ST", data.get("st"), await format_number(st_value)),
        ("V", data.get("v"), await format_number(v_value)),
        ("BOX", data.get("box"), "—"),
        ("CAS. PTS", data.get("casino_pts"), "—"),
    ]

    table = await send_table(data_for_table, total_formatted_value)

    username_text = f"@{username}" if username else ""
    text = (
        f"<b>📋 Профиль пользователя {username_text}</b> (<i>{user_id}</i>)\n\n<pre>{table}</pre>"
    )
    profile_buttons = await create_profile_buttons(user_id)
    buttons = profile_buttons if not is_admin else admins_return_buttons

    if isinstance(message, Message):
        await message.answer(text, reply_markup=buttons)
    elif isinstance(message, CallbackQuery):
        if message.message is not None and isinstance(message.message, Message):
            await message.message.edit_text(text, reply_markup=buttons)
            await message.answer()
        else:
            await message.answer(text, reply_markup=buttons)


async def send_admin_panel_message(
    user_id: int, username: str, message: CallbackQuery | Message
) -> None:
    if user_id not in config.admin_ids:
        return
    text = (
        "<b>ST-Bank | Админ-панель</b>\n\n"
        f"Добро пожаловать, @{username}\n"
        f"Текущее время: {dt.datetime.now(tz=dt.UTC).strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        "Доступные команды на данный момент:\n"
        "1. Получение списка всех юзеров\n"
        "2. Получение профиля определённого юзера\n"
        "3. Изменение любой информации о юзере\n"
        "4. Изменение цены любой валюты\n"
        "5. Рассылка сообщения\n"
        "6. Получение последних 50-ти строк логов\n"
        "7. Выключение бота\n"
    )
    if isinstance(message, Message):
        await message.answer(text, reply_markup=admin_buttons)
    elif isinstance(message, CallbackQuery):
        if message.message is not None and isinstance(message.message, Message):
            await message.message.edit_text(text, reply_markup=admin_buttons)
            await message.answer()
        else:
            await message.answer(text, reply_markup=admin_buttons)
