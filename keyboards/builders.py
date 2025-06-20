from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from config_reader import v

def calc():
    items = [
        "1", "2", "3", "/",
        "4", "5", "6", "*",
        "7", "8", "9", "-",
        "0", ".", "=", "+",
    ]

    builder = ReplyKeyboardBuilder()
    [builder.button(text=item) for item in items]
    builder.button(text="НАЗАД")
    builder.adjust(*[4] * 4)

    return builder.as_markup(resize_keyboard=True)


def profile(text: str | list):
    builder = ReplyKeyboardBuilder()

    if isinstance(text, str):
        text = [text]
    
    [builder.button(text=txt) for txt in text]
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

async def payment_keyboard(state: FSMContext):
    data = await state.get_data()
    price = int(data['amount']) * v.in_irl_rub

    builder = InlineKeyboardBuilder()
    builder.button(text=f"Оплатить {price} RUB", pay=True)
    return builder.as_markup()