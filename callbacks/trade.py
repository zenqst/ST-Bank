import asyncio

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.currencies import (
    adv_interaction,
    build_amount_prompt,
    edit_amount_handler,
    edit_currencies_handler,
    final_interaction,
    timeout_checker,
)
from database.loot import open_box
from keyboards import inline
from keyboards.inline import ActionCallback, BoxCallback, CurrencyCallback
from states.enums import CoinActions
from states.fsm_states import Interaction

router = Router()


@router.callback_query(ActionCallback.filter())
async def action_type_handler(call: CallbackQuery, callback_data: ActionCallback, bot: Bot, state: FSMContext):
    await edit_currencies_handler(state, callback_data, bot, call)


@router.callback_query(CurrencyCallback.filter())
async def currency_handler(call: CallbackQuery, callback_data: CurrencyCallback, bot: Bot, state: FSMContext):
    await edit_amount_handler(state, callback_data, bot, call)


@router.callback_query(BoxCallback.filter())
async def box_handler(call: CallbackQuery, callback_data: BoxCallback, bot: Bot, state: FSMContext):
    user_id = call.from_user.id

    await bot.answer_callback_query(call.id)

    if callback_data.type == CoinActions.BUY:
        await state.set_state(Interaction.type)
        await state.update_data(type=CoinActions.BUY)

        await state.set_state(Interaction.currency)
        await state.update_data(currency="box")

        text = await build_amount_prompt(user_id, callback_data.type, 'box')
        msg = await call.message.edit_text(text, reply_markup=inline.update_buttons)
        
        await state.set_state(Interaction.msg_id)
        await state.update_data(msg_id=msg.message_id)

        await state.set_state(Interaction.amount)

    elif callback_data.type == CoinActions.OPEN:
        await call.message.delete()
        amount = callback_data.amount

        await open_box(user_id, call, amount=amount, is_free=False)


@router.callback_query(F.data == "update")
async def update_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id

    data = await state.get_data()

    currency = data['currency']
    action = data['type']

    await bot.answer_callback_query(call.id)

    text = await build_amount_prompt(user_id, action, currency, include_diff=True)
    msg = await call.message.edit_text(text, reply_markup=inline.update_buttons)

    await state.set_state(Interaction.msg_id)
    await state.update_data(msg_id=msg.message_id)

    await state.set_state(Interaction.amount)

    asyncio.create_task(timeout_checker(bot, msg.chat.id, msg.message_id, state, timeout=120))


@router.callback_query(F.data == "agree")
async def agree_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    await state.update_data(confirmation=True)

    await final_interaction(call, state)
    await call.message.delete()
    await bot.answer_callback_query(call.id)


@router.message(Interaction.amount)
async def interaction_amount_handler(message: Message, state: FSMContext, bot: Bot):
    amount_text = message.text.replace(',', '.')    
    data = await state.get_data()
    
    try:
        amount_float = float(amount_text)

        if amount_float <= 0:
            await message.answer("❌ <b>Пожалуйста, введите положительное число больше 0</b>", reply_markup=inline.cancel_button)
        elif data['currency'] == 'box' and not amount_float.is_integer():
            await message.answer("❌ <b>Пожалуйста, введите целое число</b>", reply_markup=inline.cancel_button)
        else:
            await state.update_data(amount=amount_text)
            await adv_interaction(message, state, bot)
    except ValueError:
        await message.answer("❌ <b>Пожалуйста, введите корректное число</b>", reply_markup=inline.cancel_button)
        return