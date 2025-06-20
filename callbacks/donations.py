from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, LabeledPrice

from keyboards import builders
from config_reader import v

router = Router()

@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    amount = message.successful_payment.total_amount / 100 # перевод в рубли, поскольку по приколу делают так
    currency = message.successful_payment.currency
    payload = message.successful_payment.invoice_payload

    await message.delete()
    await message.answer(f"✅ Оплата прошла успешно! Сумма: {amount} {currency}")

async def send_invoice_handler(state: FSMContext, message: Message):
    await state.update_data(amount=message.text)
    data = await state.get_data()
    amount = data['amount']
    mult_price = int(amount) * 100 * v.in_irl_rub


    prices = [LabeledPrice(label=f"Покупка {amount}V", amount=mult_price)]
    await message.answer_invoice(
        title="Покупка валюты",
        description=f"Покупка {amount}V",
        prices=prices,
        provider_token="381764678:TEST:84879",
        payload="test-payload",
        currency="RUB",
        reply_markup=await builders.payment_keyboard(state)
    )
