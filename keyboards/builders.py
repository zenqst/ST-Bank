from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline import BoxCallback
from states.enums import CoinActions


async def create_box_button(amount: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Открыть ещё {amount} BOX", callback_data=BoxCallback(type=CoinActions.OPEN, amount=amount).pack())
    builder.adjust(1)

    return builder.as_markup()