from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.core import db
from states.enums import UserStatus, InterCurrency, CoinActions
from keyboards.inline import agree_buttons
from keyboards.reply import main
from config_reader import config, st, v

from dotenv import load_dotenv
import random as rn
from typing import Dict, List, Tuple
from json import loads, dumps

load_dotenv()

async def register(id, username) -> UserStatus:
    """
    Функция для регистрации юзера

    :param id: Айди пользователя
    :param username: Юзернейм пользователя
    :return: Базовый UserStatus
    """
    status = await check_profile(id)

    if status == UserStatus.NOT_FOUND:
        await db.insert_data("users", {"id": id, "username": username})

        return UserStatus.SUCCESS
    
    else:
        return status

async def get_profile(id) -> dict | UserStatus:
    """
    Функция для получения профиля юзера, при его отсутствии возвращает соотстветствующий UserStatus

    :param id: Айди пользователя
    :return: dict из базы данных or UserStatus
    """
    status = await check_profile(id)

    if status == UserStatus.ALREADY_EXISTS:
        data = await db.select_data("users", "*", {"id": id}, fetch_all=False)
        return data

    else:
        return status

async def check_profile(id: int) -> UserStatus:
    """
    Односложная функция, которая возвращает UserStatus

    :param id: Айди пользователя
    :return: UserStatus: ALREADT_EXISTS, NOT_FOUND or ERROR (один из)
    """

    data = await db.select_data("users", "id", {"id": id})

    if data:
        return UserStatus.ALREADY_EXISTS
    elif not data: 
        return UserStatus.NOT_FOUND
    else:
        return UserStatus.ERROR

async def diff_convert(diff: float) -> str:
    """
    Функция для конвертации чисел типа 50.3 в str "+50.3%"

    :param diff: Само число
    :return: str, состоящее из знака, числа и %
    """
    diff = round(diff, 2)

    if diff >= 0:
        text = f"+{diff}%"
    else:
        text = f"{diff}%"

    return text

async def get_price(name: str, is_round: bool = True) -> dict:
    """
    Однсложная функция, которая возвращает стоимость и разницу в цене валюты, указанную в name

    :param name: Название валюты
    :param is_round: bool-значение. При состоянии True, cost будет округляться
    :return: dict, который содержит в себе name, cost, diff
    """

    name = name.lower()
    data = await db.select_data("coins", ["cost", "diff"], {"name": name})

    if data:
        if is_round:
            cost = round(data['cost'], 2)
        else:
            cost = data['cost']

        diff = await diff_convert(data['diff'])
        new_data = {"name": name, "cost": cost, "diff": diff}

        return new_data

async def change_coin(name: str, bot: Bot) -> None:
    """
    Функция для рандомного изменения стоимости валюты по названию

    :param name: Название валюты (lower)
    :param bot: Bot
    :return: None, обновляет запись в БД
    """
    coin: object = globals()[name]
    max_growth: float = coin.max_growth
    max_fall: float = coin.max_fall
    min_price: float = float(coin.min_price)

    curr_price = await get_price(name, is_round=False)

    if curr_price['cost'] <= min_price:
        random_percent = round(rn.uniform(0.01, max_growth), 4)
    else:
        random_percent = round(rn.uniform(-max_fall, max_growth), 4)


    new_price = round(curr_price['cost'] * (1 + random_percent), 4)
    new_diff_percent = round(random_percent * 100, 4)

    if name == "v":
        await bot.send_message(config.admin_id, "<b>✅ Цена успешно изменена!</b>", reply_markup=main)
    
    await db.update_data("coins", {"cost": new_price, "diff": new_diff_percent}, {"name": name})

async def build_amount_prompt(id: int, action: CoinActions, currency: str, *, include_diff: bool = False) -> str:
    """
    Функция, конвертирующая набор данных в определённый текст (при покупке/продаже)

    :param id: Айди пользователя
    :param action: CoinActions (buy/sell)
    :param currency: Название валюты
    :param include_diff: bool-значение. При True в строчке появляется процент изменений
    :return: str-text
    """
    verb = {CoinActions.BUY:  "приобрести", CoinActions.SELL: "продать"}[action]

    user_data = await get_profile(id)
    balance, balance_label = (
        (user_data["rubles"], "RUB")
        if action == CoinActions.BUY
        else (user_data[currency], currency.upper())
    )

    price = await get_price(currency)
    diff = f"<i>({price['diff']})</i>" if include_diff else ""

    text = f"Введите количество {currency.upper()}, которое вы хотите <b>{verb}</b>\n\n<b>Текущий баланс:</b> {balance} {balance_label}\n<b>Текущая цена:</b> ~{price['cost']} RUB {diff}"

    return text

async def adv_interaction(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Функция, которая учавствует в цепочке из 2ух функций для взаимодействия с валютами. В ней первично проверяется кол-во нужной суммы у человека

    :param message: Message
    :param state: FSMContext
    :param bot: Bot
    :return: None, только присылает сообщение
    """
    user_id = message.from_user.id

    data = await state.get_data()

    currency = data['currency']
    amount = float(data['amount'])

    price_data = await get_price(currency, is_round=False)
    user_data = await get_profile(user_id)

    last_price = price_data['cost'] * amount

    await bot.delete_message(chat_id=message.chat.id, message_id=data['msg_id'])

    if amount <= 0:
        await message.answer('<b>❌ Число должно быть больше 0</b>')
        return
    elif data['type'] == CoinActions.BUY:
        if last_price > user_data['rubles']:
            await message.answer(f'<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            remaining = user_data['rubles'] - last_price
            text = f"После покупки <b>{amount} {currency.upper()}</b> на балансе останется <b>~{remaining:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    elif data['type'] == CoinActions.SELL:
        if amount > user_data[currency]:
            await message.answer(f'<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            text = f"После продажи <b>{amount} {currency.upper()}</b> на балансе прибавится <b>~{last_price:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    else:
        await message.answer(f'<b>❌ Неизвестный тип транзакции [{data['type']}]</b>')
        return
    
    await message.answer(text, reply_markup=agree_buttons)

async def final_interaction(call: CallbackQuery, state: FSMContext) -> None:
    """
    Функция, которая производит взаимодействие с валютами. Является участницей цепочки из 2ух функция

    :param call: CallbackQuery
    :param state: FSMContext
    :return: None, меняет сообщение
    """

    user_id = call.from_user.id

    data = await state.get_data()
    currency: str = data['currency']
    amount = float(data['amount'])

    price_data = await get_price(currency, is_round=False)
    user_data = await get_profile(user_id)

    last_price: float = price_data['cost'] * amount

    # TODO: много повторений в коде, надо исправить

    if amount <= 0:
        await call.message.answer('<b>❌ Число должно быть больше 0</b>')
        return
    elif data['type'] == CoinActions.BUY:
        if last_price > user_data['rubles']:
            await call.message.answer(f'<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            balance_rubles: float = user_data['rubles'] - last_price
            balance_currency: float = user_data[currency] + amount
            text = f"✅ <b>Успешная покупка {amount} {currency.upper()}!</b>\n\n<b>Баланс RUB:</b> {round(balance_rubles, 2)}\n<b>Баланс {currency.upper()}:</b> {round(balance_currency, 2)}\n<b>Цена за 1 шт. на момент транзакции:</b> {price_data['cost']} RUB\n\n<i>Не забывайте, что все акции и валюты явлюятся вымышленными</i>"
            
            await db.update_data("users", {"rubles": balance_rubles, currency: balance_currency}, {"id": user_id})

    elif data['type'] == CoinActions.SELL:
        if amount > user_data[currency]:
            await call.message.answer(f'<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            balance_rubles: float = user_data['rubles'] + last_price
            balance_currency: float = user_data[currency] - amount
            text = f"✅ <b>Успешная продажа {amount} {currency.upper()}!</b>\n\n<b>Баланс RUB:</b> {round(balance_rubles, 2)}\n<b>Баланс {currency.upper()}:</b> {round(balance_currency, 2)}\n<b>Цена за 1 шт. на момент транзакции:</b> {price_data['cost']} RUB\n\n<i>Не забывайте, что все акции и валюты явлюятся вымышленными</i>"

            await db.update_data("users", {"rubles": balance_rubles, currency: balance_currency}, {"id": user_id})

    await state.clear()
    await call.message.answer(text)

async def open_box(user_id: int, call: CallbackQuery, *, amount: int = 1, is_free: bool = False) -> None:
    """
    Функция для открытия ящиков

    :param user_id: Юзер айди 
    :param call: CallbackQuery
    :param amount: Число открытых боксов, по умолчанию равно 1
    :param is_free: При True отсутствует проверка на наличие Боксов. По умолчанию False
    :return: None 
    """

    profile = await get_profile(user_id)

    if not is_free and profile['box'] < amount:
        await call.message.answer(f'<b>❌ Недостаточно BOX для открытия!</b>\n\n<b>Баланс:</b> {profile["box"]} BOX\n<b>Требуется:</b> {amount} BOX\n\n<i>Не забывайте, что все предметы являются вымышленными. Любые совпадения — случайны</i>')
        return

    RARITY_CONFIG = {
        "legendary": {'icon': '🟡', 'chance': 0.01, 'compensation': 1100, 'order': 0},
        "mythic": {'icon': '🔴', 'chance': 2.99, 'compensation': 700, 'order': 1},
        "epic": {'icon': '🟣', 'chance': 9, 'compensation': 500, 'order': 2},
        "exotic": {'icon': '🟢', 'chance': 18, 'compensation': 300, 'order': 3},
        "common": {'icon': '⚪️', 'chance': 70, 'compensation': 200, 'order': 4},
    }

    all_items = await db.select_data("items", ["id", "name", "rarity"], fetch_all=True)
    user_data = await db.select_data("users", "items", {"id": user_id})

    user_loot = loads(user_data['items']) if user_data and user_data['items'] else []

    obtained_items = []
    boxes_left = profile['box']
    boxes_balance = profile['box']
    ruble_balance = profile['rubles']
    compensation_total = 0

    rarities = list(RARITY_CONFIG.keys())
    weights = [RARITY_CONFIG[r]['chance'] for r in rarities]

    def find_loot_item(item_id):
        for item in user_loot:
            if item.get('id') == item_id:
                return item
        return None

    for _ in range(amount):
        if boxes_left <= 0 and not is_free:
            break

        selected_rarity = rn.choices(rarities, weights=weights, k=1)[0]
        config = RARITY_CONFIG[selected_rarity]

        available_items = [item for item in all_items if str(item['rarity']).lower() == selected_rarity]
        if not available_items:
            continue

        selected_item = rn.choice(available_items)
        item_id = selected_item['id']
        item_name = selected_item['name']

        compensation_text = ""
        loot_item = find_loot_item(item_id)
        if loot_item:
            loot_item['count'] += 1
            compensation = config['compensation']
            ruble_balance += compensation
            compensation_total += compensation

            compensation_text = f"[+{compensation} RUB]"

        user_loot.append({'id': item_id, 'count': 1})
        obtained_items.append((
            selected_rarity,
            f"{config['icon']} <b>{item_name}</b> <i>{compensation_text}</i>"
        ))

        lucky = 0
        if rn.random() < 0.9:
            boxes_left -= 1
            lucky += 1
        
        

    await db.update_data('users', {
        'items': dumps(user_loot),
        'rubles': ruble_balance,
        'box': boxes_left
    }, {'id': user_id})

    obtained_items.sort(key=lambda x: RARITY_CONFIG[x[0]]['order'])
    items_text = "\n".join(item[1] for item in obtained_items) or "— ничего не выпало —"
    
    comp_text = ""

    if compensation_total > 0:
        comp_text = f"[+{compensation_total} RUB]"

    result_message = (
        "<b>🎉 Поздравляем!</b>\n\n"
        f"<i>Открыв {amount} BOX, вы получили:</i>\n"
        f"{items_text}\n\n"
        "<i>После открытия изменился ваш баланс:</i>\n"
        f"<b>Баланс RUB:</b> {round(ruble_balance, 2)} <i>{comp_text}</i>\n"
        f"<b>Баланс BOX:</b> {boxes_left} <i>[-{boxes_balance-boxes_left} BOX]</i>\n"
    )

    await call.message.answer(result_message)

async def check_casino_balance(id):
    data = await db.select_data("users", "casino_pts", {"id": id})

    return data