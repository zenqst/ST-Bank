from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config_reader import config
from keyboards.inline import BoxCallback
from states.enums import CoinActions


async def create_box_button(*, amount: int | None, box_balance: int) -> InlineKeyboardMarkup | None:
    """
    Функция, автоматически создающая клавиатуру для открытия боксов

    :param amount: Кол-во боксов (при повторном открытии)
    :param box_balance: Баланс коробочек
    :return: Клавиатурка
    """
    builder = InlineKeyboardBuilder()
    
    if not amount:
        open_options = [1, 3, 10]
        button_count = 0
        
        for option in open_options:
            if box_balance >= option:
                builder.button(text=f"Открыть {option} BOX", callback_data=BoxCallback(type=CoinActions.OPEN, amount=option).pack())
                button_count += 1
        
        builder.button(text="➕ Купить", callback_data=BoxCallback(type=CoinActions.BUY, amount=None).pack())
        builder.button(text="❌ Отменить", callback_data="cancel")
        
        if button_count > 0:
            builder.adjust(button_count, 1, 1)
        else:
            builder.adjust(1, 1)

    elif amount and box_balance >= amount:
        builder.button(text=f"Открыть ещё {amount} BOX", callback_data=BoxCallback(type=CoinActions.OPEN, amount=amount).pack())
        builder.adjust(1)

    return builder.as_markup()

# main = ReplyKeyboardMarkup(
#     keyboard=[
#         [KeyboardButton(text="📊 Торговать"),
#          KeyboardButton(text="📦 Открыть бокс"),],
#         # [KeyboardButton(text="💰 Донаты [WIP]")],
#         [KeyboardButton(text="📋 Профиль"),]
#     ],
#     resize_keyboard=True,
#     one_time_keyboard=False,
#     input_field_placeholder="Выберите действие из меню",
#     selective=True
# )


async def create_main_buttons(user_id: int) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📊 Торговать")
    builder.button(text="📦 Открыть бокс")
    builder.button(text="🎰 Игра [β]")
    builder.button(text="📋 Профиль")
    builder.adjust(2, 1, 1)
    
    if user_id in config.admin_ids:
        builder.button(text="🎛 Админ-панель")
        builder.adjust(2, 1, 1, 1)

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False, input_field_placeholder="Выберите действие из меню", selective=True)