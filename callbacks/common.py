from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.core import db
from database.loot import show_items
from database.stats import StatsManager
from keyboards.inline import bankrupt_buttons

router = Router()


@router.callback_query()
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username

    if call.message is None:
        return

    if call.data == "cancel":
        await state.clear()
        await bot.answer_callback_query(call.id)
        await call.message.edit_text('✅ <b>Действие отменено</b>')
    
    elif call.data == "items":
        await bot.answer_callback_query(call.id)
        await show_items(user_id, call)

    elif call.data == "stats":
        await bot.answer_callback_query(call.id)
        await StatsManager(user_id).show_stats(username, user_id, call)

    elif call.data == "bankrupt":
        await bot.answer_callback_query(call.id)
        await call.message.delete()

        text = (
            "<b>Процедура банкротства</b>\n\n"
            "<i>Не осталось никаких средств? Все валюты обвалились? Хотите начать свой путь заново?</i>\n\n"
            "ST Bank предлагает списать все ваши средства (каждую валюту, боксы, предметы). Благодаря этому вы сможете начать свой путь заново. Также это поможет при потере интереса к торговле на бирже.\n\n"
            "Подтвердите своё желание кнопкой ниже"
        )
        await call.message.answer(text, reply_markup=bankrupt_buttons)
    
    elif call.data == "bankrupt_agree":
        await bot.answer_callback_query(call.id)
        await call.message.delete()

        await db.delete_data("users", {"id": user_id})

        text = (
            "<b>💸 Процедура банкротства прошла успешно</b>\n\n"
            "Процедура завершилась, ваш аккаунт был удалён из базы ST Bank в связи с полный обнулением. Зарегистрируйтесь заново через /start"
        )
        await call.message.answer(text)