from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery, LabeledPrice
from aiogram.fsm.context import FSMContext

from keyboards import builders
from config_reader import v
from data.datebase import update_data, get_profile

router = Router()

# ✅ 1. Обработка подтверждения чекаута
@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    await query.answer(ok=True)


# ✅ 2. Обработка успешной оплаты
@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")

    if amount is None:
        await message.answer("⚠️ Не удалось обработать оплату: отсутствует сумма.")
        return

    try:
        amount = int(amount)
    except ValueError:
        await message.answer("⚠️ Некорректное значение суммы.")
        return

    user_id = message.from_user.id
    username = message.from_user.username
    balance = get_profile(user_id, username)

    # 💾 Увеличиваем баланс на amount
    update_data("users", {"v": balance[2] + amount})

    await state.clear()
    await message.answer(f"<b>✅ Оплата прошла успешно!</b>\n\nНа счёт добавлено {amount}V")


# ✅ 3. Отправка счёта (инвойса)
async def send_invoice_handler(state: FSMContext, message: Message):
    # ⛔️ Игнорируем сообщения с успешной оплатой
    if message.successful_payment:
        return

    await state.update_data(amount=message.text)
    data = await state.get_data()
    amount = data.get("amount")

    if amount is None:
        await message.answer("⚠️ Не удалось получить сумму.")
        return

    try:
        amount = int(amount)
        mult_price = amount * 100 * v.in_irl_rub
    except ValueError:
        await message.answer("⚠️ Некорректное значение суммы.")
        return

    prices = [LabeledPrice(label=f"Покупка {amount}V", amount=mult_price)]

    await message.answer_invoice(
        title=f"Покупка {amount}V",
        description=(
            "Оплачивая покупку, вы соглашаетесь с тем, что донаты являются формой поощрения автора "
            "в обмен на приятный бонус. Деньги не подлежат возврату.\n\n"
            "Для тестов используйте карту: 1111 1111 1111 1026, 12/22, CVC 000\n"
        ),
        prices=prices,
        provider_token="381764678:TEST:84879",
        payload="test-payload",
        currency="RUB",
        reply_markup=await builders.payment_keyboard(state)
    )
