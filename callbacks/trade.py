from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
import asyncio

from database.queries import (
    adv_interaction,
    build_amount_prompt,
    final_interaction,
    open_box,
    timeout_checker
)
from keyboards import inline
from keyboards.inline import ActionCallback, BoxCallback, CurrencyCallback
from states.enums import CoinActions
from states.fsm_states import Interaction

router = Router()


@router.callback_query(ActionCallback.filter())
async def action_type_handler(call: CallbackQuery, callback_data: ActionCallback, bot: Bot, state: FSMContext):
    await state.set_state(Interaction.type)  # приводим в активность type из interaction
    await state.update_data(type=callback_data.action_type)

    await bot.answer_callback_query(call.id)
    await call.message.edit_text('Выберите валюту для взаимодействия\n\n<b>Краткая сводка:</b>\n<b>ST</b> — валюта для начинающих, является более стабильной. Помогает новичкам обрести свой первый капитал.\n<b>V</b> — валюта, которая уже является более реалистичной. В ней цена может в любой момент обвалиться почти в 0, а может, и вырасти на тысячи рублей.', reply_markup=inline.choose_currency_buttons)


@router.callback_query(CurrencyCallback.filter())
async def currency_handler(call: CallbackQuery, callback_data: CurrencyCallback, bot: Bot, state: FSMContext):
    user_id = call.from_user.id

    interaction_data = await state.get_data()
    await state.set_state(Interaction.currency)
    await bot.answer_callback_query(call.id)

    currency = callback_data.currency
    await state.update_data(currency=currency)

    text = await build_amount_prompt(user_id, interaction_data['type'], currency)

    msg = await call.message.edit_text(text, reply_markup=inline.update_buttons)

    await state.set_state(Interaction.msg_id)
    await state.update_data(msg_id=msg.message_id)

    await state.set_state(Interaction.amount)

    asyncio.create_task(timeout_checker(bot, msg.chat.id, msg.message_id, state, timeout=120))


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
    
    try:
        amount_float = float(amount_text)

        if amount_float > 0:
            await state.update_data(amount=amount_text)
            await adv_interaction(message, state, bot)
        else:
            await message.answer("❌ <b>Пожалуйста, введите положительное число больше 0</b>", reply_markup=inline.cancel_button)
    except ValueError:
        await message.answer("❌ <b>Пожалуйста, введите корректное число</b>", reply_markup=inline.cancel_button)
        return