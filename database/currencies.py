import asyncio
import math
import secrets
import random as rn

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config_reader import Coin, st, v
from database.core import db
from database.messages import send_for_admins
from database.stats import StatsManager
from database.user import get_profile
from database.utils import get_price
from keyboards.inline import (
    ActionCallback,
    CurrencyCallback,
    ReturnCallback,
    agree_buttons,
    choose_currency_buttons,
    update_buttons,
)
from states.enums import CoinActions, Currencies
from states.fsm_states import Interaction
from states.types import CurrencyInfo, CurrencyKey


async def create_action_msg(currency: Currencies, *, balance: float | None, currency_info: CurrencyInfo, action_word: str | None, profit: float | None) -> str:
    actions = ["покупка", "продажа"]
    currency_str = currency.value.upper()
    if action_word is None:
        text = (
            f"<b>❌ Недостаточно {currency_str}!</b>\n\n"
            f"<b>Баланс:</b> {round(currency_info['balance'], 2)} {currency_str}\n"
            f"<b>Требуется:</b> {currency_info['amount']} {currency_str}\n"
        )
    elif action_word.lower() in actions:
        if currency_info['amount'] is None or currency_info['cost'] is None or balance is None:
            text = (
                "<b>❌ Неизвестная ошибка!</b>\n"
                "Обратитесь к администратору!\n"
            )
        else:
            text = (
                f"✅ <b>Успешная {action_word} {currency_info['amount']} {currency_str}!</b>\n\n"
                f"<b>Баланс RUB:</b> {round(balance, 2)}\n"
                f"<b>Баланс {currency_str}:</b> {round(currency_info['balance'], 2)}\n"
                f"<b>Цена за единицу:</b> {currency_info['cost']} RUB\n"
            )
            if profit:
                text += f"<b>Прибыль:</b> {round(profit, 2)} RUB\n"
    else:
        text = (
            "<b>❌ Неизвестная ошибка!</b>\n\n"
            "Обратитесь к администратору!\n"
        )
    text += "\n<i>Не забывайте, что все предметы и валюты являются вымышленными. Любые совпадения — случайны</i>"
    return text


async def edit_currencies_handler(state: FSMContext, callback_data: ActionCallback | ReturnCallback, bot: Bot, call: CallbackQuery) -> None:
    await state.set_state(Interaction.type)
    if isinstance(callback_data, ActionCallback):
        await state.update_data(type=callback_data.action_type)
    await bot.answer_callback_query(call.id)
    text = (
        "Выберите валюту для взаимодействия\n\n"
        "<b>Краткая сводка:</b>\n"
        "<b>ST</b> — валюта для начинающих, является более стабильной. Помогает новичкам обрести свой первый капитал.\n"
        "<b>V</b> — валюта, которая уже является более реалистичной. В ней цена может в любой момент обвалиться почти в 0, а может, и вырасти на тысячи рублей."
    )
    await call.message.edit_text(text, reply_markup=choose_currency_buttons)


async def build_amount_prompt(user_id: int, action: CoinActions, currency: CurrencyKey, *, include_diff: bool = False) -> str:
    verb = {CoinActions.BUY: "приобрести", CoinActions.SELL: "продать"}[action]
    user_data = await get_profile(user_id)
    balance, balance_label = (
        (user_data["rubles"], "RUB") if action == CoinActions.BUY else (user_data[currency], currency.upper())
    )
    price = await get_price(currency)
    diff = f"<i>({price['diff']})</i>" if include_diff else ""
    max_rounded = math.floor(balance / price['cost'] * 100) / 100
    text = (
        f"Введите количество {currency.upper()}, которое вы хотите <b>{verb}</b>\n\n"
        f"<b>Текущий баланс:</b> {round(balance, 2)} {balance_label}\n"
        f"<b>Текущая цена:</b> ~{price['cost']} RUB {diff}\n"
    )
    if action == CoinActions.BUY:
        text += f"<b>Максимально возможное кол-во:</b> {max_rounded} {currency.upper()}"
    return text


async def edit_amount_handler(state: FSMContext, callback_data: CurrencyCallback, bot: Bot, call: CallbackQuery) -> None:
    user_id = call.from_user.id
    interaction_data = await state.get_data()
    await state.set_state(Interaction.currency)
    await bot.answer_callback_query(call.id)
    currency = callback_data.currency
    await state.update_data(currency=currency)
    text = await build_amount_prompt(user_id, interaction_data['type'], currency)
    msg = await call.message.edit_text(text, reply_markup=update_buttons)
    await state.set_state(Interaction.msg_id)
    await state.update_data(msg_id=msg.message_id)
    await state.set_state(Interaction.amount)
    asyncio.create_task(timeout_checker(bot, msg.chat.id, msg.message_id, state, timeout=120))


async def timeout_checker(bot: Bot, chat_id: int, message_id: int, state: FSMContext, timeout: int):
    await asyncio.sleep(timeout)
    current_state = await state.get_state()
    if current_state in {Interaction.amount.state, Interaction.confirmation.state}:
        await state.clear()
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="⏰<b> Время ожидания ответа истекло</b>",
                reply_markup=None,
            )
        except TelegramBadRequest as e:
            if "message to edit not found" in str(e).lower():
                # ignore
                pass
            else:
                raise


async def adv_interaction(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user is None:
        return
    user_id = message.from_user.id
    data = await state.get_data()
    currency: CurrencyKey = data['currency']
    amount = float(data['amount'])
    price_data = await get_price(currency, is_round=False)
    user_data = await get_profile(user_id)
    last_price = price_data['cost'] * amount
    await bot.delete_message(chat_id=message.chat.id, message_id=data['msg_id'])
    if data['type'] == CoinActions.BUY:
        if last_price > user_data['rubles']:
            currency_info: CurrencyInfo = {
                'balance': user_data['rubles'],
                'cost': None,
                'amount': last_price,
            }
            text = await create_action_msg(
                Currencies.RUB,
                balance=None,
                currency_info=currency_info,
                action_word=None,
                profit=None,
            )
            await message.answer(text)
            return
        else:
            remaining = user_data['rubles'] - last_price
            text = f"После покупки <b>{amount} {currency.upper()}</b> на балансе останется <b>~{remaining:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    elif data['type'] == CoinActions.SELL:
        if amount > user_data[currency]:
            currency_info = {
                'balance': user_data[currency],
                'cost': None,
                'amount': amount,
            }
            text = await create_action_msg(
                Currencies(currency),
                balance=user_data['rubles'],
                currency_info=currency_info,
                action_word=None,
                profit=None,
            )
            await message.answer(text)
            return
        else:
            text = f"После продажи <b>{amount} {currency.upper()}</b> на балансе прибавится <b>~{last_price:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    else:
        await message.answer(f'<b>❌ Неизвестный тип транзакции [{data["type"]}]</b>')
        return
    await state.set_state(Interaction.confirmation)
    msg = await message.answer(text, reply_markup=agree_buttons)
    asyncio.create_task(timeout_checker(bot, msg.chat.id, msg.message_id, state, timeout=120))


async def final_interaction(call: CallbackQuery, state: FSMContext) -> None:
    if call.message is None:
        return
    user_id = call.from_user.id
    data = await state.get_data()
    currency: CurrencyKey = data['currency']
    amount = float(data['amount'])
    price_data = await get_price(currency, is_round=False)
    user_data = await get_profile(user_id)
    last_price: float = price_data['cost'] * amount
    profit = None
    stats = StatsManager(user_id)
    await stats.load()
    if data['type'] == CoinActions.BUY:
        if last_price > user_data['rubles']:
            currency_info: CurrencyInfo = {
                'balance': user_data['rubles'],
                'cost': None,
                'amount': last_price,
            }
            text = await create_action_msg(Currencies.RUB, balance=None, currency_info=currency_info, action_word=None, profit=None)
            await call.message.answer(text)
            return
        balance_rubles = user_data['rubles'] - last_price
        balance_currency = user_data[currency] + amount
        action_word = "покупка"
        await stats.record_buy(currency, amount, price_data['cost'])
    elif data['type'] == CoinActions.SELL:
        if amount > user_data[currency]:
            currency_info = {
                'balance': user_data[currency],
                'cost': None,
                'amount': amount,
            }
            text = await create_action_msg(Currencies(currency), balance=user_data['rubles'], currency_info=currency_info, action_word=None, profit=None)
            await call.message.answer(text)
            return
        balance_rubles = user_data['rubles'] + last_price
        balance_currency = user_data[currency] - amount
        action_word = "продажа"
        profit = await stats.record_sell(currency, amount, price_data['cost'])
    else:
        await call.message.answer(f'<b>❌ Неизвестный тип транзакции [{data["type"]}]</b>')
        return
    currency_info: CurrencyInfo = {'balance': balance_currency, 'cost': price_data['cost'], 'amount': amount}
    text = await create_action_msg(Currencies(currency), balance=balance_rubles, currency_info=currency_info, action_word=action_word, profit=profit)
    await db.update_data("users", {"rubles": balance_rubles, currency: balance_currency}, {"id": user_id})
    await stats.save()
    await state.clear()
    await call.message.answer(text)


async def change_trend_score(name: str, score: float) -> None:
    data = await get_price(name)
    new_score: float = (data['trend_score'] + score) * 0.9
    new_score = max(min(new_score, 100), -100)
    await db.update_data("coins", {"trend_score": new_score}, {"name": name})


async def secure_uniform(a: float, b: float) -> float:
    scale = 10 ** 8
    rand = secrets.randbelow(int((b - a) * scale)) / scale
    return a + rand


async def change_coin(name: str, bot: Bot) -> None:
    coins_map = {'st': st, 'v': v}
    coin: Coin = coins_map[name]
    max_growth: float = coin.max_growth
    max_fall: float = coin.max_fall
    min_price: float = coin.min_price
    min_growth: float = coin.min_growth
    min_fall: float = coin.min_fall
    coin_info = await get_price(name, is_round=False)
    trend_score: float = coin_info['trend_score']
    score = abs(trend_score)
    chance = min(100, score)
    roll = secrets.randbelow(100) + 1
    try:
        if roll <= chance:
            random_percent = round(max_growth, 4) if trend_score > 0 else round(-max_fall, 4)
            await send_for_admins(f"{name} резко изменилась в цене (chance: {round(trend_score, 2)}%)!")
            await change_trend_score(name, 0)
        elif coin_info['cost'] <= min_price or secrets.choice([True, False]):
            random_percent = round(await secure_uniform(min_growth, max_growth), 4)
            await change_trend_score(name, random_percent * 10)
        else:
            random_percent = -round(await secure_uniform(min_fall, max_fall), 4)
            await change_trend_score(name, random_percent * 10)
        new_price = round(coin_info['cost'] * (1 + random_percent), 4)
        new_diff_percent = round(random_percent * 100, 4)
        await db.update_data("coins", {"cost": new_price, "diff": new_diff_percent}, {"name": name})
    except Exception:
        await send_for_admins("❌ Произошла ошибка во время изменения цены")


async def calculate_precise_growth_chance(name: str, simulations: int = 10000) -> float:
    coin_info = await get_price(name, is_round=False)
    trend_score: float = coin_info['trend_score']
    coins_map = {'st': st, 'v': v}
    coin = coins_map[name]
    up_count = 0
    for _ in range(simulations):
        chance = min(100, abs(trend_score))
        roll = secrets.randbelow(100) + 1
        if roll <= chance:
            if trend_score > 0:
                up_count += 1
        elif coin_info['cost'] <= coin.min_price or secrets.choice([True, False]):
            up_count += 1
    return (up_count / simulations) * 100


async def change_all_coins(bot: Bot):
    """
    Простая функция, которая получает рандомное время от 2.5 до 5 минут, а потом обновляет валюты
    """
    random_time = rn.randint(150, 300)

    await change_coin('st', bot)
    await change_coin('v', bot)
    await asyncio.sleep(random_time)

