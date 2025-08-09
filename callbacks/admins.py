from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.core import db
from keyboards.inline import AdminCallback, admins_return_buttons

router = Router()


@router.callback_query(AdminCallback.filter())
async def coins_handler(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: AdminCallback):
    user_id = call.from_user.id
    username = call.from_user.username

    if call.message is None:
        return
    
    if callback_data.action == "get_all_users":
        await bot.answer_callback_query(call.id)
        text = ""

        users = await db.select_data("users", "*", fetch_all=True)

        for i, user in enumerate(users):
            username = user.get("username")
            user_id = user.get("id")
            text += f"{i + 1}. @{username} ({user_id})\n"
        
        text += f"\nОбщее кол-во пользователей: {len(users)}"
    
    await call.message.edit_text(text, reply_markup=admins_return_buttons)