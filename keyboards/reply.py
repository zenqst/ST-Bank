from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

register = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💲 Открыть брокерский счёт"),]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите действие из меню",
    selective=True
)

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Торговать"),
         KeyboardButton(text="📦 Открыть бокс"),],
        [KeyboardButton(text="💰 Донаты")],
        [KeyboardButton(text="📋 Профиль"),]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Выберите действие из меню",
    selective=True
)

rkr = ReplyKeyboardRemove()