from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from states.enums import CoinActions, InterCurrency

class ActionCallback(CallbackData, prefix="type"):
    action_type: CoinActions

class CurrencyCallback(CallbackData, prefix="curr"):
    currency: str

class BoxCallback(CallbackData, prefix="box"):
    type: CoinActions
    amount: None | int

profile_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📜 Список предметов", callback_data='items')
        ],
        [
            InlineKeyboardButton(text="📥 Написать разработчику", url="tg://resolve?domain=zenqst")
        ]
    ]
)

action_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Купить", callback_data=ActionCallback(action_type = CoinActions.BUY).pack()),
            InlineKeyboardButton(text="➖ Продать", callback_data=ActionCallback(action_type = CoinActions.SELL).pack())
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

box_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Открыть x1", callback_data=BoxCallback(type=CoinActions.OPEN, amount=1).pack()),
            InlineKeyboardButton(text="Открыть x3", callback_data=BoxCallback(type=CoinActions.OPEN, amount=3).pack()),
            InlineKeyboardButton(text="Открыть x10", callback_data=BoxCallback(type=CoinActions.OPEN, amount=10).pack()),
        ],
        [
            InlineKeyboardButton(text="➕ Купить", callback_data=BoxCallback(type=CoinActions.BUY, amount=None).pack()),
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"),
        ],
    ]
)

items_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Вернуться", callback_data='return_profile')
        ],
    ]
)
