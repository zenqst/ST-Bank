from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class ActionCallback(CallbackData, prefix="type"):
    action_type: str

class CurrencyCallback(CallbackData, prefix="cur"):
    currency: str

class BoxCallback(CallbackData, prefix="box"):
    type: str
    amount: None | int 

choose_type_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Купить", callback_data=ActionCallback(action_type = "buy").pack()),
            InlineKeyboardButton(text="➖ Продать", callback_data=ActionCallback(action_type = "sell").pack())
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
)

choose_currency_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="ST", callback_data=CurrencyCallback(currency = "st").pack()),
            InlineKeyboardButton(text="V", callback_data=CurrencyCallback(currency = "v").pack()),
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
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
            InlineKeyboardButton(text="Открыть x1", callback_data=BoxCallback(type = "opening", amount = 1).pack()),
            InlineKeyboardButton(text="Открыть x3", callback_data=BoxCallback(type = "opening", amount = 3).pack()),
            InlineKeyboardButton(text="Открыть x10", callback_data=BoxCallback(type = "opening", amount = 10).pack())
        ],
        [
            InlineKeyboardButton(text="➕ Купить", callback_data=BoxCallback(type = "buy", amount=None).pack())
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
)

cancel_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
)

agree_buy_box_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data='agree_buy_box'),
            InlineKeyboardButton(text="✏️ Изменить", callback_data='edit_buy_box'),
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
)

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

items_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Вернуться", callback_data='return_profile')
        ],
        [
            InlineKeyboardButton(text='🗄 График изменений валют', url='https://docs.google.com/spreadsheets/d/13eaUPw-ceQUmeU31WwC4MiU4kM7-RCwPgbzco-xCuAA/edit?usp=sharing')
        ],
        [
            InlineKeyboardButton(text="📥 Написать разработчику", url="tg://resolve?domain=zenqst")
        ]
    ]
)