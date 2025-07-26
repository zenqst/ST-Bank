import asyncio
import logging
import math
import random as rn
import secrets
from json import dumps, loads
from typing import Any

import prettytable as pt
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from asyncpg.exceptions import PostgresError
from dotenv import load_dotenv
from millify import millify

from config_reader import Coin, config, st, v
from database.core import db
from keyboards.builders import create_box_button
from keyboards.inline import agree_buttons, items_buttons, profile_buttons
from keyboards.reply import main
from states.enums import CoinActions, Currencies, UserStatus
from states.types import CurrencyInfo, CurrencyKey, ProfileData, TableProfile

load_dotenv()
logger = logging.getLogger(__name__)


async def register(user_id: int, username: str) -> UserStatus:
    """
    Функция для регистрации юзера

    :param id: Айди пользователя
    :param username: Юзернейм пользователя
    :return: Базовый UserStatus
    """
    status = await check_profile(user_id)

    if status == UserStatus.NOT_FOUND:
        await db.insert_data("users", {"id": user_id, "username": username})

        return UserStatus.SUCCESS
    
    else:
        return status


async def get_profile(user_id: int) -> ProfileData:
    """
    Функция для получения профиля юзера

    :param id: Айди пользователя
    :return: ProfileData из базы данных
    """
    # не чекаем наличие юзера, поскольку его не может не быть на данном этапе

    data = await db.select_data("users", "*", {"id": user_id}, fetch_all=False)
    return data


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


async def create_action_msg(currency: Currencies, *, balance: float | None, currency_info: CurrencyInfo, action_word: str | None) -> str:
    """
    Функция, которая преобразует данные в строку с уведомлением об успешной покупке или же недостатке средств

    :param currency: Валюта
    :param balance: Баланс RUB
    :param currency_info: Словарь CurrencyInfo (balance, cost, amount) или (balance, need) для недостатка средств
    :param action_word: "покупка" или "продажа"
    :return: Соответствующая строка
    """
    actions = ['покупка', 'продажа']
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
    else:
        text = (
            "<b>❌ Неизвестная ошибка!</b>\n\n"
            "Обратитесь к администратору!\n"
        )
    text += "\n<i>Не забывайте, что все предметы и валюты являются вымышленными. Любые совпадения — случайны</i>"
    return text


async def get_price(name: str, is_round: bool = True) -> dict:
    """
    Однсложная функция, которая возвращает стоимость и разницу в цене валюты, указанную в name

    :param name: Название валюты
    :param is_round: bool-значение. При состоянии True, cost будет округляться
    :return: dict, который содержит в себе name, cost, diff, trend_score
    """

    name = name.lower()
    data = await db.select_data("coins", ["cost", "diff", "trend_score"], {"name": name})

    cost = round(data['cost'], 2) if is_round else data['cost']

    diff = await diff_convert(data['diff'])
    new_data = {"name": name, "cost": cost, "diff": diff, "trend_score": data['trend_score']}

    return new_data
    

async def change_trend_score(name: str, score: float) -> None:
    data = await get_price(name)

    new_score: float = (data['trend_score'] + score) * 0.9
    new_score = max(min(new_score, 100), -100)

    await db.update_data("coins", {"trend_score": new_score}, {"name": name})


async def secure_uniform(a: float, b: float) -> float:
    """Безопасный аналог random.uniform для float."""
    # secrets.randbelow работает только с int, поэтому имитируем float:
    scale = 10**8
    rand = secrets.randbelow(int((b - a) * scale)) / scale
    return a + rand


async def change_coin(name: str, bot: Bot) -> None:
    """
    Функция для безопасного изменения стоимости валюты по названию.

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

    roll = secrets.randbelow(100) + 1  # 1–100 включительно

    if roll <= chance:
        random_percent = round(max_growth, 4) if trend_score > 0 else round(-max_fall, 4)
        await bot.send_message(
            config.admin_id,
            f"<b>Валюта {name} резко изменила цену из-за trend points ({trend_score})</b>",
            reply_markup=main
        )
        await change_trend_score(name, 0)
    elif coin_info['cost'] <= min_price or secrets.choice([True, False]):
        random_percent = round(await secure_uniform(min_growth, max_growth), 4)
        await change_trend_score(name, random_percent * 10)
    else:
        random_percent = -round(await secure_uniform(min_fall, max_fall), 4)
        await change_trend_score(name, random_percent * 10)

    new_price = round(coin_info['cost'] * (1 + random_percent), 4)
    new_diff_percent = round(random_percent * 100, 4)

    if name == "v":
        await bot.send_message(config.admin_id, "<b>✅ Цена успешно изменена!</b>", reply_markup=main)

    await db.update_data("coins", {"cost": new_price, "diff": new_diff_percent}, {"name": name})


async def calculate_precise_growth_chance(name: str, simulations: int = 10000) -> float:
    """
    Высокоточная оценка вероятности роста через симуляцию.
    """
    coin_info = await get_price(name, is_round=False)
    trend_score: float = coin_info['trend_score']
    
    coins_map = {'st': st, 'v': v}
    coin = coins_map[name]
    
    up_count = 0
    
    for _ in range(simulations):
        chance = min(100, abs(trend_score))
        roll = secrets.randbelow(100) + 1
        
        if roll <= chance:
            # Тренд сработал
            if trend_score > 0:
                up_count += 1
        # Случайное изменение
        elif coin_info['cost'] <= coin.min_price or secrets.choice([True, False]):
            up_count += 1
            # иначе падение, не считаем
    
    return (up_count / simulations) * 100


async def build_amount_prompt(user_id: int, action: CoinActions, currency: CurrencyKey, *, include_diff: bool = False) -> str:
    """
    Функция, конвертирующая набор данных в определённый текст (при покупке/продаже)

    :param user_id: Айди пользователя
    :param action: CoinActions (buy/sell)
    :param currency: Название валюты
    :param include_diff: bool-значение. При True в строчке появляется процент изменений
    :return: str-text
    """

    verb = {CoinActions.BUY: "приобрести", CoinActions.SELL: "продать"}[action]

    user_data = await get_profile(user_id)
    balance, balance_label = (
        (user_data["rubles"], "RUB")
        if action == CoinActions.BUY
        else (user_data[currency], currency.upper())
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


async def adv_interaction(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Функция, которая учавствует в цепочке из 2ух функций для взаимодействия с валютами. В ней первично проверяется кол-во нужной суммы у человека

    :param message: Message
    :param state: FSMContext
    :param bot: Bot
    :return: None, только присылает сообщение
    """
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

    if amount <= 0:
        await message.answer('<b>❌ Число должно быть больше 0</b>')
        return
    elif data['type'] == CoinActions.BUY:
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
                action_word=None
            )

            await message.answer(text)
            return
        else:
            remaining = user_data['rubles'] - last_price
            text = f"После покупки <b>{amount} {currency.upper()}</b> на балансе останется <b>~{remaining:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    elif data['type'] == CoinActions.SELL:
        if amount > user_data[currency]:
            currency_info: CurrencyInfo = {
                'balance': user_data[currency],
                'cost': None,
                'amount': amount,
            }

            text = await create_action_msg(
                Currencies(currency),
                balance=user_data['rubles'],
                currency_info=currency_info,
                action_word=None
            )

            await message.answer(text)
            return
        else:
            text = f"После продажи <b>{amount} {currency.upper()}</b> на балансе прибавится <b>~{last_price:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    else:
        await message.answer(f'<b>❌ Неизвестный тип транзакции [{data["type"]}]</b>')
        return
    
    await message.answer(text, reply_markup=agree_buttons)


async def final_interaction(call: CallbackQuery, state: FSMContext) -> None:
    """
    Функция, которая производит взаимодействие с валютами. Является участницей цепочки из 2ух функций

    :param call: CallbackQuery
    :param state: FSMContext
    :return: None, меняет сообщение
    """

    if call.message is None:
        return

    user_id = call.from_user.id
    data = await state.get_data()
    currency: CurrencyKey = data['currency']
    amount = float(data['amount'])

    price_data = await get_price(currency, is_round=False)
    user_data = await get_profile(user_id)
    last_price: float = price_data['cost'] * amount

    if amount <= 0:
        await call.message.answer('<b>❌ Число должно быть больше 0</b>')
        return

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
                action_word=None
            )

            await call.message.answer(text)
            return
        balance_rubles = user_data['rubles'] - last_price
        balance_currency = user_data[currency] + amount
        action_word = "покупка"
    elif data['type'] == CoinActions.SELL:
        if amount > user_data[currency]:
            currency_info: CurrencyInfo = {
                'balance': user_data[currency],
                'cost': None,
                'amount': amount,
            }

            text = await create_action_msg(
                Currencies(currency),
                balance=user_data['rubles'],
                currency_info=currency_info,
                action_word=None
            )

            await call.message.answer(text)
            return
        balance_rubles = user_data['rubles'] + last_price
        balance_currency = user_data[currency] - amount
        action_word = "продажа"
    else:
        await call.message.answer(f'<b>❌ Неизвестный тип транзакции [{data["type"]}]</b>')
        return

    currency_info: CurrencyInfo = {
        'balance': balance_currency,
        'cost': price_data['cost'],
        'amount': amount,
    }

    text = await create_action_msg(
        Currencies(currency),
        balance=balance_rubles,
        currency_info=currency_info,
        action_word=action_word
    )

    await db.update_data(
        "users",
        {"rubles": balance_rubles, currency: balance_currency},
        {"id": user_id},
    )
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


async def get_available_items_by_rarity(all_items: list[dict], rarity_name: str) -> list[dict]:
    """
    Получить список предметов по редкости

    :param all_items: Список всех предметов
    :param rarity_name: Название редкости (str)
    :return: Список предметов указанной редкости
    """
    return [item for item in all_items if str(item['rarity']) == rarity_name]


async def handle_loot_item(user_loot: list[dict], item_id: int, rarity_conf: dict, ruble_balance: dict[str, int | float]) -> str:
    """
    Обработать добавление предмета в инвентарь пользователя,
    начислить компенсацию если предмет уже есть

    :param user_loot: Список предметов пользователя
    :param item_id: ID предмета
    :param rarity_conf: Конфигурация редкости предмета
    :param ruble_balance: Баланс рублей (с компенсацией)
    :return: Текст компенсации для вывода в сообщении
    """
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
    return compensation_text


async def process_box_rewards(amount: int, boxes_balance: dict[str, int], ruble_balance: dict[str, int | float], user_loot: list[dict[str, Any]], is_free: bool) -> list[tuple[str, str]]:
    """
    Функция, которая открывает указанное количество боксов и возвращает список полученных предметов
    
    :param amount: Количество открываемых боксов
    :param boxes_balance: Текущий баланс боксов
    :param ruble_balance: Баланс RUB
    :param user_loot: Инвентарь пользователя
    :param is_free: Если True, не тратит боксы
    :return: Список кортежей (редкость, описание предмета)
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
        available_items = await get_available_items_by_rarity(all_items, rarity_name)

        if not available_items:
            continue

        selected_item = rn.choice(available_items)
        item_id = selected_item['id']
        item_name = selected_item['name']

        compensation_text = await handle_loot_item(user_loot, item_id, rarity_conf, ruble_balance)

        obtained_items.append((
            selected_rarity,
            f"{rarity_conf['icon']} <b>{item_name}</b> <i>{compensation_text}</i>"
        ))

        if secrets.randbelow(1_000_000) / 1_000_000 > lucky_chance and not is_free:
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

    if call.message is None:
        return

    profile = await get_profile(user_id)

    if not is_free and profile['box'] < amount:
        currency_info: CurrencyInfo = {
                'balance': profile['box'],
                'cost': None,
                'amount': amount,
            }

        text = await create_action_msg(
            Currencies.BOX,
            balance=None,
            currency_info=currency_info,
            action_word=None
        )
        
        await call.message.answer(text)
        return

    user_data = await db.select_data("users", "items", {"id": user_id})
    user_loot = loads(user_data['items']) if user_data and user_data['items'] else []

    boxes_balance: dict[str, int] = {"balance": profile['box'], "left": profile['box']}
    ruble_balance: dict[str, int | float] = {"balance": profile['rubles'], "compensation": 0}
    obtained_items = await process_box_rewards(amount, boxes_balance, ruble_balance, user_loot, is_free)

    await update_box_data(user_loot, ruble_balance['balance'], boxes_balance['left'], user_id)

    result_message = await create_result_message(obtained_items, amount, ruble_balance, boxes_balance)

    inline_kb = await create_box_button(amount=amount, box_balance=boxes_balance['left'])
    await call.message.answer(result_message, reply_markup=inline_kb)


def _generate_user_items_text(available_items: list[dict], user_items_dict: dict[int, int]) -> str:
    """Генерирует текст для предметов, которые есть у пользователя"""
    lines = []
    for item in available_items:
        count = user_items_dict.get(item['id'], 0)
        if count > 0:
            lines.append(f"{item['name']} <i>[{count} шт.]</i>")
    return "\n".join(lines)


async def build_rarity_section(
    rarity_key: str,
    info: dict,
    all_items: list[dict],
    user_items_dict: dict[int, int]
) -> str:
    """
    Строит текст для одной редкости с учётом предметов пользователя

    :param rarity_key: Ключ редкости
    :param info: Информация о редкости (name, icon, chance, order)
    :param all_items: Список всех предметов
    :param user_items_dict: Словарь {item_id: count} пользователя
    :return: Текст для данной редкости
    """
    name = info['display_name']
    icon = info['icon']
    chance = info['chance']

    section_text = f"<b>{icon} {name} ({chance}%):</b> — "
    available_items = [item for item in all_items if item['rarity'] == rarity_key]
    item_count = len(available_items)

    if not user_items_dict:
        return section_text + f"0 из {item_count}\n<i>Не открыто ни одного предмета редкости</i>\n\n"

    count_with_user = sum(1 for item in available_items if user_items_dict.get(item['id'], 0) > 0)

    if count_with_user == 0:
        section_text += f"0 из {item_count}\n<i>Не открыто ни одного предмета редкости</i>\n\n"
    else:
        section_text += f"<b>{count_with_user}</b> из {item_count}\n"
        section_text += _generate_user_items_text(available_items, user_items_dict)

    section_text += "\n\n"
    return section_text


async def show_items(user_id: int, call: CallbackQuery):
    all_items = await db.select_data("items", ["id", "name", "rarity"], fetch_all=True)
    res = await db.select_data("users", ["items"], {"id": user_id})

    user_loot = loads(res['items']) if res and res['items'] else []

    user_items_dict = {}
    for user_item in user_loot:
        user_items_dict[user_item['id']] = user_items_dict.get(user_item['id'], 0) + user_item.get('count', 0)

    text = ""
    for rarity_key, info in sorted(config.rarities.items(), key=lambda x: x[1]['order']):
        section = await build_rarity_section(rarity_key, info, all_items, user_items_dict)
        text += section

    if isinstance(call.message, Message):
        return await call.message.edit_text(text, reply_markup=items_buttons)
    else:
        return


async def change_all_coins(bot: Bot):
    """
    Простая функция, которая получает рандомное время от 2.5 до 5 минут, а потом обновляет валюты
    """
    random_time = rn.randint(150, 300)

    await change_coin('st', bot)
    await change_coin('v', bot)
    await asyncio.sleep(random_time)


async def format_number(num: float) -> str:
    """
    Функция, трансформирующая числа типа 123456.78 -> 123.45K. Числа ниже 100К не трогает

    :param num: float число
    :return: Строка со значением
    """
    treshold_to_shorten = 100_000

    if abs(num) < treshold_to_shorten:
        s = f"{num:.2f}".rstrip('0').rstrip('.')
        return s
    
    return millify(num, precision=2)


async def send_table(data: list[tuple[str, int | float | str, str]], total_sum: str) -> pt.PrettyTable:
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
        table.add_row([symbol, f'{await format_number(amount)}' if isinstance(amount, (float)) else amount, cost])

    table.add_row(['-' * 10, '-' * 10, '-' * 15])

    table.add_row(['TOTAL', '', f'~{total_sum} RUB'])

    return table


async def send_profile(user_id: int, username: str | None, message: Message | CallbackQuery) -> None:
    """
    Функция для отправки сообщения с профилем

    :param user_id: Айди юзера
    :param username: Никнейм юзера
    :param message: Message или CallbackQuery (зависит от расположения функции)
    :return: None
    """

    data: ProfileData = await get_profile(user_id)

    st_price = await get_price("st")
    v_price = await get_price("v")

    st_value: float = st_price['cost'] * data['st']
    v_value: float = v_price['cost'] * data['v']
    total_value = data['rubles'] + st_value + v_value
    total_formatted_value = await format_number(total_value)

    data_for_table: TableProfile = [
        ('RUB', data['rubles'], '—'),
        ('ST', data['st'], await format_number(st_value)),
        ('V', data['v'], await format_number(v_value)),
        ('BOX', data['box'], '—')
    ]

    table = await send_table(data_for_table, total_formatted_value)

    username_text = f"@{username}" if username else ""

    text = f"<b>📋 Профиль пользователя {username_text}</b> (<i>{user_id}</i>)\n\n<pre>{table}</pre>"

    if isinstance(message, Message):
        await message.answer(text, reply_markup=profile_buttons)
    elif isinstance(message, CallbackQuery):
        if message.message is not None and isinstance(message.message, Message):
            await message.message.edit_text(text, reply_markup=profile_buttons)
            await message.answer()
        else:
            await message.answer(text, reply_markup=profile_buttons)


async def send_single_message(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(user_id, text)
        await asyncio.sleep(0.05)
    except TelegramAPIError as e:
        logger.warning("Не удалось отправить сообщение пользователю %d: %s", user_id, e)
        raise


async def send_broadcast_message(state: FSMContext, bot: Bot) -> None:
    try:
        all_users: list[dict[str, Any]] = await db.select_data("users", "*", fetch_all=True)
    except PostgresError:
        logger.exception("Ошибка при получении списка пользователей: %s")
        return

    if not all_users:
        await bot.send_message(config.admin_id, "Нет пользователей для рассылки.")
        return

    successful = 0
    failed = 0
    tasks = []
    data = await state.get_data()
    text = data['sending_text']

    for user in all_users:
        user_id = user.get("id")
        if not user_id:
            logger.warning("Пропущен пользователь без ID: %s", user)
            failed += 1
            continue

        task = asyncio.create_task(send_single_message(bot, user_id, text))
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.error("Ошибка при отправке сообщения: %s", result)
            failed += 1
        else:
            successful += 1

    try:
        await bot.send_message(
            config.admin_id,
            f"Рассылка завершена!\n\n✅ Успешно: {successful}\n❌ Не отправлено: {failed}"
        )
    except TelegramAPIError:
        logger.exception("Не удалось отправить отчёт админу: %s")

    await state.clear()


async def check_casino_balance(user_id):
    data = await db.select_data("users", "casino_pts", {"id": user_id})

    return data