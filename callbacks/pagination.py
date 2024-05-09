from contextlib import suppress

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from keyboards import fabrics
from data.datebase import select_data

router = Router()