from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

st_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Купить", callback_data='buy'),
            InlineKeyboardButton(text="➖ Продать", callback_data="sell")
        ]
    ]
)

buy_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="ST", callback_data='buy_st'),
            InlineKeyboardButton(text="🆕 V", callback_data="buy_v")
        ]
    ]
)

sell_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="ST", callback_data='sell_st'),
            InlineKeyboardButton(text="🆕 V", callback_data="sell_v")
        ]
    ]
)

agree_buy_st_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data='agree_buy_st'),
            InlineKeyboardButton(text="✏️ Изменить", callback_data='edit_buy_st'),
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
)

agree_sell_st_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data='agree_sell_st'),
            InlineKeyboardButton(text="✏️ Изменить", callback_data='edit_sell_st'),
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
)

agree_buy_v_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data='agree_buy_v'),
            InlineKeyboardButton(text="✏️ Изменить", callback_data='edit_buy_v'),
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
)

agree_sell_v_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data='agree_sell_v'),
            InlineKeyboardButton(text="✏️ Изменить", callback_data='edit_sell_v'),
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ]
)

profile_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🔕 Уведомления выключены [PRO]", callback_data='none') # Добавить!!!
        ],
        [
            InlineKeyboardButton(text="✉️ Написать разработчику", url="tg://resolve?domain=zenq_st")
        ]
    ]
)