from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

profile_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📜 Список предметов", callback_data='items')
        ],
        [
            InlineKeyboardButton(text='🗄 График изменений валют', url='https://docs.google.com/spreadsheets/d/13eaUPw-ceQUmeU31WwC4MiU4kM7-RCwPgbzco-xCuAA/edit?usp=sharing')
        ],
        [
            InlineKeyboardButton(text="📥 Написать разработчику", url="tg://resolve?domain=zenqst")
        ]
    ]
)
