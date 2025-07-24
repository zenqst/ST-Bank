import random as rn
from asyncio import sleep as asleep
from json import dumps, loads
from typing import Any

import prettytable as pt
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

from config_reader import Coin, config, st, v
from database.core import db
from keyboards.inline import agree_buttons, profile_buttons
from keyboards.reply import main
from states.enums import CoinActions, UserStatus

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

    text = f"+{diff}%" if diff >= 0 else f"{diff}%"

    return text


async def get_price(name: str, is_round: bool = True) -> dict | None:
    """
    Однсложная функция, которая возвращает стоимость и разницу в цене валюты, указанную в name

    :param name: Название валюты
    :param is_round: bool-значение. При состоянии True, cost будет округляться
    :return: dict, который содержит в себе name, cost, diff, trend_score
    """

    name = name.lower()
    data = await db.select_data("coins", ["cost", "diff", "trend_score"], {"name": name})

    if data:
        cost = round(data['cost'], 2) if is_round else data['cost']

        diff = await diff_convert(data['diff'])
        new_data = {"name": name, "cost": cost, "diff": diff, "trend_score": data['trend_score']}

        return new_data


async def change_trend_score(name: str, new_score: float) -> None:
    data = await get_price(name)

    new_score: float = (data['trend_score'] + new_score) * 0.9
    new_score = max(min(new_score, 100), -100)

    await db.update_data("coins", {"trend_score": new_score}, {"name": name})


async def change_coin(name: str, bot: Bot) -> None:
    """
    Функция для рандомного изменения стоимости валюты по названию

    :param name: Название валюты (lower)
    :param bot: Bot
    :return: None, обновляет запись в БД
    """
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

    roll = rn.uniform(1, 100)

    if roll <= chance:
        random_percent = round(max_growth, 4) if trend_score > 0 else round(-max_fall, 4)

        await bot.send_message(config.admin_id, f"<b>Валюта {name} резко изменила цену из-за trend points ({trend_score})</b>", reply_markup=main)
        await change_trend_score(name, 0)
    elif coin_info['cost'] <= min_price or rn.choice([True, False]):
        random_percent = round(rn.uniform(min_growth, max_growth), 4)
        await change_trend_score(name, random_percent * 10)
    else:
        random_percent = round(-rn.uniform(min_fall, max_fall), 4)
        await change_trend_score(name, random_percent * 10)

    new_price = round(coin_info['cost'] * (1 + random_percent), 4)
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
    verb = {CoinActions.BUY: "приобрести", CoinActions.SELL: "продать"}[action]

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
            await message.answer('<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            remaining = user_data['rubles'] - last_price
            text = f"После покупки <b>{amount} {currency.upper()}</b> на балансе останется <b>~{remaining:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    elif data['type'] == CoinActions.SELL:
        if amount > user_data[currency]:
            await message.answer('<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            text = f"После продажи <b>{amount} {currency.upper()}</b> на балансе прибавится <b>~{last_price:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    else:
        await message.answer(f'<b>❌ Неизвестный тип транзакции [{data["type"]}]</b>')
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
            await call.message.answer('<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            balance_rubles: float = user_data['rubles'] - last_price
            balance_currency: float = user_data[currency] + amount
            text = f"✅ <b>Успешная покупка {amount} {currency.upper()}!</b>\n\n<b>Баланс RUB:</b> {round(balance_rubles, 2)}\n<b>Баланс {currency.upper()}:</b> {round(balance_currency, 2)}\n<b>Цена за 1 шт. на момент транзакции:</b> {price_data['cost']} RUB\n\n<i>Не забывайте, что все акции и валюты явлюятся вымышленными</i>"
            
            await db.update_data("users", {"rubles": balance_rubles, currency: balance_currency}, {"id": user_id})

    elif data['type'] == CoinActions.SELL:
        if amount > user_data[currency]:
            await call.message.answer('<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            balance_rubles: float = user_data['rubles'] + last_price
            balance_currency: float = user_data[currency] - amount
            text = f"✅ <b>Успешная продажа {amount} {currency.upper()}!</b>\n\n<b>Баланс RUB:</b> {round(balance_rubles, 2)}\n<b>Баланс {currency.upper()}:</b> {round(balance_currency, 2)}\n<b>Цена за 1 шт. на момент транзакции:</b> {price_data['cost']} RUB\n\n<i>Не забывайте, что все акции и валюты явлюятся вымышленными</i>"

            await db.update_data("users", {"rubles": balance_rubles, currency: balance_currency}, {"id": user_id})

    await state.clear()
    await call.message.answer(text)


async def find_loot_item(user_loot: list[dict[str, Any]], item_id: int) -> dict[str, Any] | None:
    for item in user_loot:
        if item.get('id') == item_id:
            return item
    return None


async def update_box_data(user_loot: list[dict[str, Any]], ruble_balance: float, boxes_left: float, user_id: int) -> None:
    """
    Простая функция, которая обновляет данные о пользователе, связанные с Боксами

    :param user_loot: Ожидаем user_loot
    :param ruble_balance: Ожидаем текущий баланс рублей (с компенсацией)
    :param boxes_left: Ожидаем boxes_balance['left']
    :param user_id: Айди юзера
    :return: None
    """

    await db.update_data('users', {
            'items': dumps(user_loot),
            'rubles': ruble_balance,
            'box': boxes_left
        }, {'id': user_id})


async def create_result_message(obtained_items: list[tuple[str, str]], amount: int, ruble_balance: dict[str, int | float], boxes_balance: dict[str, int]) -> str:
    """
    Функция, которая превращает некоторые данные в сообщение об открытии боксов

    :param obtained_items: Список предметов
    :param ruble_balance: dict с рублями
    :param boxes_balance: dict с боксами
    :return: Сообщение для вывода
    """

    obtained_items.sort(key=lambda x: config.rarities[x[0]]['order'])
    items_text = "\n".join(item[1] for item in obtained_items) or "— ничего не выпало —"

    comp_text = f"[+{ruble_balance['compensation']} RUB]" if ruble_balance['compensation'] > 0 else ""

    boxes_compensation = boxes_balance['balance'] - boxes_balance['left']

    result_message = (
        "<b>🎉 Поздравляем!</b>\n\n"
        f"<i>После открытия {amount} BOX, вы получили:</i>\n"
        f"{items_text}\n\n"
        "<i>После открытия изменился ваш баланс:</i>\n"
        f"<b>Баланс RUB:</b> {round(ruble_balance['balance'], 2)} <i>{comp_text}</i>\n"
        f"<b>Баланс BOX:</b> {boxes_balance['left']} <i>[-{boxes_compensation} BOX]</i>\n"
    )

    return result_message


async def process_box_rewards(amount: int, boxes_balance: dict[str, int], ruble_balance: dict[str, int | float], user_loot: list[dict[str, Any]], is_free: bool) -> list[tuple[str, str]]:
    """
    Функция, которая открывает указанное количество боксов и возвращает список полученных предметов
    
    :param amount: Количество открываемых боксов
    :param boxes_balance: Текущий баланс боксов
    :param ruble_balance: Баланс RUB
    :param user_loot: Инвентарь пользователя
    :param is_free: Если True, не тратит боксы
    :return: Список кортежей
    """
    
    obtained_items = []
    all_items = await db.select_data("items", ["id", "name", "rarity"], fetch_all=True)
    rarities = list(config.rarities.keys())
    weights = [config.rarities[r]['chance'] for r in rarities]
    lucky_chance = 0.1  # 10%

    for _ in range(amount):
        if boxes_balance['balance'] <= 0 and not is_free:
            break

        selected_rarity = rn.choices(rarities, weights=weights, k=1)[0]
        rarity_conf = config.rarities[selected_rarity]

        rarity_name = rarity_conf['name']
        available_items = [item for item in all_items if str(item['rarity']) == rarity_name]

        if not available_items:
            continue

        selected_item = rn.choice(available_items)
        item_id = selected_item['id']
        item_name = selected_item['name']

        compensation_text = ""
        loot_item = await find_loot_item(user_loot, item_id)
        if loot_item:
            loot_item['count'] += 1
            compensation = rarity_conf['compensation']
            ruble_balance['compensation'] += compensation
            ruble_balance['balance'] += compensation
            compensation_text = f"[+{compensation} RUB]"
        else:
            user_loot.append({'id': item_id, 'count': 1})

        obtained_items.append((
            selected_rarity,
            f"{rarity_conf['icon']} <b>{item_name}</b> <i>{compensation_text}</i>"
        ))

        if rn.random() > lucky_chance and not is_free:
            boxes_balance['left'] -= 1

    return obtained_items


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
        await call.message.answer(
            f"<b>❌ Недостаточно BOX для открытия!</b>\n\n"
            f"<b>Баланс:</b> {profile['box']} BOX\n"
            f"<b>Требуется:</b> {amount} BOX\n\n"
            f"<i>Не забывайте, что все предметы являются вымышленными. Любые совпадения — случайны</i>"
        )
        return

    user_data = await db.select_data("users", "items", {"id": user_id})
    user_loot = loads(user_data['items']) if user_data and user_data['items'] else []

    boxes_balance: dict[int, int] = {"balance": profile['box'], "left": profile['box']}
    ruble_balance: dict[float, int | float] = {"balance": profile['rubles'], "compensation": 0}
    obtained_items = await process_box_rewards(amount, boxes_balance, ruble_balance, user_loot, is_free)

    await update_box_data(user_loot, ruble_balance['balance'], boxes_balance['left'], user_id)

    result_message = await create_result_message(obtained_items, amount, ruble_balance, boxes_balance)

    await call.message.answer(result_message)


async def show_items(user_id: int, call: CallbackQuery, inline: InlineKeyboardMarkup):
    all_items = await db.select_data("items", ["id", "name", "rarity"], fetch_all=True)
    res = await db.select_data("users", ["items"], {"id": user_id})

    user_loot = loads(res['items']) if res and res['items'] else []

    user_items_dict = {}
    for user_item in user_loot:
        user_items_dict[user_item['id']] = user_items_dict.get(user_item['id'], 0) + user_item.get('count', 0)

    text = ""
    for rarity_key, info in sorted(config.rarities.items(), key=lambda x: x[1]['order']):
        name = info['name']
        icon = info['icon']
        chance = info['chance']

        text += f"<b>{icon} {name} ({chance}%):</b> — "

        available_items = [item for item in all_items if item['rarity'] == rarity_key]
        item_count = len(available_items)

        if user_items_dict:
            count_with_user = sum(1 for item in available_items if user_items_dict.get(item['id'], 0) > 0)

            if count_with_user == 0:
                text += f"0 из {item_count}\n<i>Не открыто ни одного предмета редкости</i>\n"
            else:
                text += f"<b>{count_with_user}</b> из {item_count}\n"
                for item in available_items:
                    if user_items_dict.get(item['id'], 0) > 0:
                        count = user_items_dict.get(item['id'], 0)
                        text += f"{item['name']} <i>[{count} шт.]</i>\n"
        else:
            text += f"0 из {item_count}\n<i>Не открыто ни одного предмета редкости</i>\n"

        text += "\n"

    return await call.message.edit_text(text, reply_markup=inline.items_buttons)


async def change_all_coins(bot: Bot):
    """
    Простая функция, которая получает рандомное время от 2.5 до 5 минут, а потом обновляет валюты
    """
    random_time = rn.randint(150, 300)

    await change_coin('st', bot)
    await change_coin('v', bot)
    await asleep(random_time)


async def send_table(data: list[tuple[str, int | float | str, str]], total_sum: float) -> pt.PrettyTable:
    """
    Функция для создания таблицы из данных в профиле

    :param data: Список данных о валютах
    :param total_sum: Переменная, которая содержит подсчёт всего NET WORTH
    :return: Таблица (prettyTable)
    """

    table = pt.PrettyTable(['Название', 'Количество', 'Стоимость'])
    table.align['Название'] = 'l'
    table.align['Количество'] = 'r'
    table.align['Стоимость'] = 'r'

    for symbol, amount, cost in data:
        table.add_row([symbol, f'{amount:.2f}' if isinstance(amount, (int, float)) else amount, cost])

    table.add_row(['-' * 10, '-' * 10, '-' * 15])

    table.add_row(['TOTAL', '', f'~{total_sum:.2f} RUB'])

    return table


async def send_profile(user_id: int, username: str, message: Message | CallbackQuery) -> None:
    """
    Функция для отправки сообщения с профилем

    :param user_id: Айди юзера
    :param username: Никнейм юзера
    :param message: Message или CallbackQuery (зависит от расположения функции)
    :return: None
    """

    data = await get_profile(user_id)

    st_price = await get_price("st")
    v_price = await get_price("v")

    st_value = st_price['cost'] * data['st']
    v_value = v_price['cost'] * data['v']
    total_value = data['rubles'] + st_value + v_value

    table = await send_table([
        ('RUB', data['rubles'], '—'),
        ('ST', data['st'], f'~{round(st_value, 2)} RUB'),
        ('V', data['v'], f'~{round(v_value, 2)} RUB'),
        ('BOX', data['box'], '—')
    ], total_value)

    text = f"<b>📋 Профиль пользователя @{username}</b> (<i>{user_id}</i>)\n\n<pre>{table}</pre>"

    if isinstance(message, Message):
        await message.answer(text, reply_markup=profile_buttons)
    elif isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=profile_buttons)
        await message.answer()


async def check_casino_balance(user_id):
    data = await db.select_data("users", "casino_pts", {"id": user_id})

    return data