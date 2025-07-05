from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.core import db
from states.enums import UserStatus

from dotenv import load_dotenv

load_dotenv()

async def register(id, username) -> UserStatus:
    """
    Функция для регистрации юзера

    :param id: Айди пользователя
    :param username: Юзернейм пользователя
    :return: Базовый UserStatus
    """
    status = await check_profile(id)

    if status == UserStatus.NOT_FOUND:
        db.insert_data("users", {"id": id, "username": username})

        return UserStatus.SUCCESS
    
    else:
        return status

async def get_profile(id) -> list | UserStatus:
    """
    Функция для получения профиля юзера, при его отсутствии отсылает UserStatus

    :param id: Айди пользователя
    :return: list из базы данных or UserStatus
    """
    status = await check_profile(id)

    if status == UserStatus.ALREADY_EXISTS:
        data = await db.select_data("users", "*", {"id": id})
        return data

    else:
        return status

async def check_profile(id: int) -> UserStatus:
    """
    Односложная функция, которая возвращает UserStatus

    :param id: Айди пользователя
    :return: UserStatus: ALREADT_EXISTS, NOT_FOUND or ERROR (один из)
    """

    data = await db.select_data("users", "id", {"id": id})

    if data:
        return UserStatus.ALREADY_EXISTS
    elif not data: 
        return UserStatus.NOT_FOUND
    else:
        return UserStatus.ERROR