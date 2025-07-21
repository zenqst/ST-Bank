from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from states.enums import InterActions, InterCurrency

class ActionCallback(CallbackData, prefix="type"):
    action_type: InterActions

class CurrencyCallback(CallbackData, prefix="curr"):
    currency: str

profile_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📜 Список предметов [WIP]", callback_data='items')
        ],
        [
            InlineKeyboardButton(text='🗄 График изменений валют [WIP]', url='https://docs.google.com/spreadsheets/d/13eaUPw-ceQUmeU31WwC4MiU4kM7-RCwPgbzco-xCuAA/edit?usp=sharing')
        ],
        [
            InlineKeyboardButton(text="📥 Написать разработчику", url="tg://resolve?domain=zenqst")
        ]
    ]
)

action_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Купить", callback_data=ActionCallback(action_type = InterActions.BUY).pack()),
            InlineKeyboardButton(text="➖ Продать", callback_data=ActionCallback(action_type = InterActions.SELL).pack())
        ],
        [
            InlineKeyboardButton(text='❌ Отменить', callback_data='cancel')
        ],
    ]
)

choose_currency_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="ST", callback_data=CurrencyCallback(currency = InterCurrency.ST).pack()),
            InlineKeyboardButton(text="V", callback_data=CurrencyCallback(currency = InterCurrency.V).pack())
        ],
        [
            InlineKeyboardButton(text='❌ Отменить', callback_data='cancel')
        ],
    ]
)

update_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Получить текущую цену", callback_data="update")
        ],
        [
            InlineKeyboardButton(text='❌ Отменить', callback_data='cancel')
        ],
    ]
)

last_chance_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔝 Купить максимальное кол-во валюты", callback_data="update")
        ],
        [
            InlineKeyboardButton(text='❌ Отменить', callback_data='cancel')
        ],
    ]
)

agree_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="agree"),
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
)
