from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.core import db
from states.enums import UserStatus, InterActions, InterCurrency, BoxRarity
from keyboards.inline import agree_buttons
from config_reader import config, st, v

from dotenv import load_dotenv
from random import uniform, randint, random, choices, choice
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
        random_percent = round(uniform(0.01, max_growth), 4)
    else:
        random_percent = round(uniform(-max_fall, max_growth), 4)


    new_price = round(curr_price['cost'] * (1 + random_percent), 4)
    new_diff_percent = round(random_percent * 100, 4)

    if name == "v":
        await bot.send_message(config.admin_id, "<b>✅ Цена успешно изменена!</b>")
    
    await db.update_data("coins", {"cost": new_price, "diff": new_diff_percent}, {"name": name})

async def build_amount_prompt(id: int, action: InterActions, currency: str, *, include_diff: bool = False) -> str:
    """
    Функция, конвертирующая набор данных в определённый текст (при покупке/продаже)

    :param id: Айди пользователя
    :param action: InterActions (buy/sell)
    :param currency: Название валюты
    :param include_diff: bool-значение. При True в строчке появляется процент изменений
    :return: str-text
    """
    verb = {InterActions.BUY:  "приобрести", InterActions.SELL: "продать"}[action]

    user_data = await get_profile(id)
    balance, balance_label = (
        (user_data["rubles"], "RUB")
        if action == InterActions.BUY
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

    print(f"💰 user_data['rubles'] type: {type(user_data['rubles'])}, value: {user_data['rubles']}")

    last_price = price_data['cost'] * amount

    await bot.delete_message(chat_id=message.chat.id, message_id=data['msg_id'])

    if amount <= 0:
        await message.answer('<b>❌ Число должно быть больше 0</b>')
        return
    elif data['type'] == InterActions.BUY:
        if last_price > user_data['rubles']:
            await message.answer(f'<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            remaining = user_data['rubles'] - last_price
            text = f"После покупки <b>{amount}{currency.upper()}</b> на балансе останется <b>~{remaining:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    elif data['type'] == InterActions.SELL:
        if amount > user_data[currency]:
            await message.answer(f'<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            text = f"После продажи <b>{amount}{currency.upper()}</b> на балансе прибавится <b>~{last_price:.2f} RUB</b>\nПодтвердите покупку кнопками ниже.\n\n<i>Напоминаем, что в любой момент транзакции цена может измениться, а значит, надо действовать как можно быстрее</i>"
    
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
    elif data['type'] == InterActions.BUY:
        if last_price > user_data['rubles']:
            await call.message.answer(f'<b>❌ Недостаточно средств для совершения транзакции</b>')
            return
        else:
            balance_rubles: float = user_data['rubles'] - last_price
            balance_currency: float = user_data[currency] + amount
            text = f"✅ <b>Успешная покупка {amount} {currency.upper()}!</b>\n\n<b>Баланс RUB:</b> {round(balance_rubles, 2)}\n<b>Баланс {currency.upper()}:</b> {round(balance_currency, 2)}\n<b>Цена за 1 шт. на момент транзакции:</b> {price_data['cost']} RUB\n\n<i>Не забывайте, что все акции и валюты явлюятся вымышленными</i>"
            
            await db.update_data("users", {"rubles": balance_rubles, currency: balance_currency}, {"id": user_id})

    elif data['type'] == InterActions.SELL:
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

RARITY_CONFIG: Dict[BoxRarity, Dict] = {
    BoxRarity.LEGENDARY: {
        'icon': '🟡',
        'chance': 1,
        'compensation': 1100,
        'order': 0
    },
    BoxRarity.MYTHIC: {
        'icon': '🔴',
        'chance': 4,
        'compensation': 700,
        'order': 1
    },
    BoxRarity.EPIC: {
        'icon': '🟣',
        'chance': 20,
        'compensation': 500,
        'order': 2
    },
    BoxRarity.EXOTIC: {
        'icon': '🟢',
        'chance': 30,
        'compensation': 300,
        'order': 3
    },
    BoxRarity.COMMON: {
        'icon': '⚪️',
        'chance': 45,
        'compensation': 200,
        'order': 4
    }
}

async def open_box(user_id: int, message: Message, *, amount: int = 1, is_free: bool = False) -> None:
    profile = await get_profile(id)

    if profile['boxes'] < amount and is_free == False:
        await message.answer(f'⚠️ Недостаточно боксов! У вас: {profile['boxes']}, нужно: {amount}')
        return

    RARITY_CONFIG = {
        "Легендарная": {
            'icon': '🟡',
            'chance': 1,
            'compensation': 1100,
            'order': 0
        },
        "Мифическая": {
            'icon': '🔴',
            'chance': 4,
            'compensation': 700,
            'order': 1
        },
        "Эпическая": {
            'icon': '🟣',
            'chance': 20,
            'compensation': 500,
            'order': 2
        },
        "Экзотическая": {
            'icon': '🟢',
            'chance': 30,
            'compensation': 300,
            'order': 3
        },
        "Обычная": {
            'icon': '⚪️',
            'chance': 45,
            'compensation': 200,
            'order': 4
        }
    }

    all_items = await db.select_data("loot", ["id", "name", "rarity"], fetch_all=True)
    user_data = await db.select_data("users", ["loot"], {"id": user_id})
    
    user_loot = loads(user_data['loot']) if user_data and user_data['loot'] else []
    existing_ids = {item['id'] for item in user_loot if item.get('exist')}

    # Подготовка структур для результатов
    obtained_items = []
    boxes_left = profile['boxes']
    st_balance = profile['st']
    compensation_total = 0
    new_items = []

    # Подготовка данных для случайного выбора
    rarities = list(RARITY_CONFIG.keys())
    weights = [RARITY_CONFIG[r]['chance'] for r in rarities]

    # Главный цикл открытия боксов
    for _ in range(amount):
        # Выбор редкости
        selected_rarity = choices(rarities, weights=weights, k=1)[0]
        config = RARITY_CONFIG[selected_rarity]
        
        # Выбор предмета
        available_items = [item for item in all_items if item[2] == selected_rarity]
        if not available_items:
            continue
            
        selected_item = choice(available_items)
        item_id, item_name, _ = selected_item
        
        # Проверка дубликата
        if item_id in existing_ids:
            # Обработка дубликата
            compensation = config['compensation']
            st_balance += compensation
            compensation_total += compensation
            obtained_items.append((
                selected_rarity,
                f"{config['icon']} <b>{item_name}</b> (повторка +{compensation}ST)"
            ))
            boxes_left -= 1  # Бокс тратится всегда для дубликата
        else:
            # Новый предмет
            new_items.append({'id': item_id, 'exist': True})
            existing_ids.add(item_id)
            obtained_items.append((
                selected_rarity,
                f"{config['icon']} <b>{item_name}</b>"
            ))
            
            # Механика сохранения бокса (50% шанс)
            if random() < 0.5:
                boxes_left -= 1  # Бокс тратится только в 50% случаев

    # Обновление данных пользователя
    if new_items:
        user_loot.extend(new_items)
        await db.update_data('users', {
            'loot': dumps(user_loot),
            'st': st_balance,
            'boxes': boxes_left
        }, {'id': user_id})
    else:
        await db.update_data('users', {
            'st': st_balance,
            'boxes': boxes_left
        }, {'id': user_id})

    # Сортировка результатов
    obtained_items.sort(key=lambda x: RARITY_CONFIG[x[0]]['order'])
    items_text = "\n".join(item[1] for item in obtained_items)

    # Формирование ответа
    result_message = (
        "<b>🎉 Поздравляем!</b>\n\n"
        "📦 Вы получили:\n"
        f"{items_text}\n\n"
        f"💰 ST: {st_balance} | 📦 Боксы: {boxes_left}"
    )
    
    if compensation_total > 0:
        result_message += f"\n\n🎁 Компенсация за повторки: +{compensation_total}ST"
    
    await message.answer(result_message)

async def check_casino_balance(id):
    data = await db.select_data("users", "casino_pts", {"id": id})

    return data