from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from states.enums import CoinActions, Currencies


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
            InlineKeyboardButton(text="💸 Стать банкротом", callback_data="bankrupt")
        ],
        [
            InlineKeyboardButton(text="📥 Написать разработчику", url="tg://resolve?domain=zenqst")
        ]
    ]
)

bankrupt_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💔 Обанкротиться", callback_data='bankrupt_agree')
        ],
        [
            InlineKeyboardButton(text='❌ Отменить', callback_data='cancel')
        ],
    ]
)

action_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Купить", callback_data=ActionCallback(action_type=CoinActions.BUY).pack()),
            InlineKeyboardButton(text="➖ Продать", callback_data=ActionCallback(action_type=CoinActions.SELL).pack())
        ],
        [
            InlineKeyboardButton(text='❌ Отменить', callback_data='cancel')
        ],
    ]
)

choose_currency_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="ST", callback_data=CurrencyCallback(currency=Currencies.ST).pack()),
            InlineKeyboardButton(text="V", callback_data=CurrencyCallback(currency=Currencies.V).pack())
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

items_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Вернуться", callback_data='return_profile')
        ],
    ]
)
