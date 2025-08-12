from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from states.enums import CoinActions, Currencies, Steps


class ActionCallback(CallbackData, prefix="type"):
    action_type: CoinActions


class CurrencyCallback(CallbackData, prefix="curr"):
    currency: str


class BoxCallback(CallbackData, prefix="box"):
    type: CoinActions
    amount: None | int


class ReturnCallback(CallbackData, prefix="return"):
    prev_step: Steps


class AdminCallback(CallbackData, prefix="adm"):
    action: str


profile_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика аккаунта", callback_data='stats'),
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
            InlineKeyboardButton(text="🔙 Вернуться", callback_data=ReturnCallback(prev_step=Steps.ACTIONS).pack())
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
            InlineKeyboardButton(text="🔙 Вернуться", callback_data=ReturnCallback(prev_step=Steps.CURRENCIES).pack())
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
            InlineKeyboardButton(text="🔙 Вернуться", callback_data=ReturnCallback(prev_step=Steps.PROFILE).pack())
        ],
    ]
)

cancel_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ],
    ]
)

admin_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍👩‍👦‍👦 Получить список всех юзеров", callback_data=AdminCallback(action="get_all_users").pack()),
            InlineKeyboardButton(text="👤 Получить профиль юзера", callback_data=AdminCallback(action="get_user").pack())
        ],
        [
            InlineKeyboardButton(text="💸 Измененить цену валюты", callback_data=AdminCallback(action="change_coin").pack())
        ],
        [
            InlineKeyboardButton(text="📨 Сделать рассылку", callback_data=AdminCallback(action="start_mailing").pack())
        ],
        [
            InlineKeyboardButton(text="📜 Получить логи", callback_data=AdminCallback(action="get_logs").pack())
        ],
        [
            InlineKeyboardButton(text="🔄 Перезапустить бота", callback_data=AdminCallback(action="restart_bot").pack()),
            InlineKeyboardButton(text="🔴 Выключить бота", callback_data=AdminCallback(action="stop_bot").pack())
        ]
    ]
)

admins_return_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data=ReturnCallback(prev_step=Steps.ADMIN).pack())
        ],
    ]
)

admin_currency_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="ST", callback_data=AdminCallback(action=Currencies.ST).pack()),
            InlineKeyboardButton(text="V", callback_data=AdminCallback(action=Currencies.V).pack())
        ],
        [
            InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data=ReturnCallback(prev_step=Steps.ADMIN).pack())
        ],
    ]
)