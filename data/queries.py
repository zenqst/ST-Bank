from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from dotenv import load_dotenv

from config_reader import st, v

from data.google_sheets import add_to_table
from data.core import db

from keyboards import inline, reply

from utils.enums import UserStatus

import random

from config_reader import config
import json

load_dotenv()

# img = open('data/box_open.gif', 'rb')

not_register = '⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.'

async def register(id, username) -> UserStatus:
    """
    Функция регистрации пользователя

    :param id: Передаём user_id
    :param username: Передаём username
    :return: UserStatus (ENUM)
    """
    status = await get_profile(id)

    if status == UserStatus.NOT_FOUND:
        await db.insert_data('users', {'id': id, 'username': username, 'ruble': 2000, 'st': 10, 'v': 5})
        return UserStatus.SUCCESS
    else:
        return UserStatus.ALREADY_EXISTS
    
async def get_profile(id) -> list | UserStatus:
    """
    Функция получения профиля

    :param id: Передаём user_id
    :return: list (id[0], username[1], ruble[2], st[3], v[4], boxes[5], loot[6]) **OR** UserStatus.NOT_FOUND
    """

    data = await db.select_data('users', "*", {'id': id})

    if data:
        return data
    else:
        return UserStatus.NOT_FOUND

async def get_price(name):
    data = await db.select_data('coins', ['curr_price', 'diff_percent'], {'name': name})
    return data

async def last_interaction(id: int, username: str, state: FSMContext):
    data = await state.get_data()
    currency = data['currency']
    amount = float(data['amount'])

    price_data = await get_price(currency)
    price = float(price_data[0]) * amount

    balance = await get_profile(id, username)

    if currency == "st":
        balance_index = 1
    elif currency == "v":
        balance_index = 2
    else:
        balance_index = 3

    currency_balance = balance[balance_index]

    if data['currency'] == 'box' and data['type'] == 'buy':
        if price > balance[1]:
            await state.clear()
            return f'❌ <b>Недостаточно средств</b>\n\nНеобходимо: {price}ST (Баланс: {balance[1]}ST)'
        await db.update_data('users', {'st': balance[1] - price}, {'id': id})
        await db.update_data('users', {'boxes': currency_balance + int(amount)}, {'id': id})
        return f'✅ <b>Успешно!</b>\n\nВы приобрели <b>{amount} 📦</b> за <b>{price}ST</b>'
    elif data['type'] == 'buy':
        if price > balance[0]:
            await state.clear()
            return f'❌ <b>Недостаточно средств</b>\n\nНеобходимо: {price}₽ (Баланс: {balance[0]}₽)'
        await db.update_data('users', {'ruble': balance[0] - price}, {'id': id})
        await db.update_data('users', {currency: currency_balance + int(amount)}, {'id': id})
        return f'✅ <b>Успешно!</b>\n\nВы приобрели <b>{amount}{currency.upper()}</b> за <b>{price}₽</b>'
    else:
        if amount > currency_balance:
            await state.clear()
            return f'❌ <b>Недостаточно акций</b>\n\nНеобходимо: {amount}{currency.upper()} (Баланс: {currency_balance}{currency.upper()})'
        await db.update_data('users', {'ruble': balance[0] + price}, {'id': id})
        await db.update_data('users', {currency: currency_balance - int(amount)}, {'id': id})
        return f'✅ <b>Успешно!</b>\n\nВы продали <b>{amount}{currency.upper()}</b> за <b>{price}₽</b>'

async def change_coin(name: str, bot: Bot):
    coin = globals()[name]  # Получаем модуль динамически
    max_growth = getattr(coin, 'max_growth')
    max_fall = getattr(coin, 'max_fall')

    random_percent = round(random.uniform(-max_fall, max_growth), 2)

    data = await get_price(name)

    new_price = round(data[0] + data[0] * random_percent, 2)
    new_diff_percent = round(random_percent * 100, 2)

    if float(new_price) <= float(getattr(coin, 'min_price')):
        new_price = float(getattr(coin, 'min_price')) + float(random.randint(0, 100))

    # print(f'{name}\nЦена до: {data[0]}\nЦена после: {new_price}\nПроцент: {new_diff_percent}\n')

    await add_to_table(name, new_price)

    if name == "v":
        await bot.send_message(config.admin_id, f'✅ <b>Цена успешно изменена!</b>')

    await db.update_data('coins', {'curr_price': new_price, 'diff_percent': new_diff_percent}, {'name': name})

async def advanced_interaction(state: FSMContext, message: Message):
    await state.update_data(amount=message.text)
    user_id = message.from_user.id
    username = message.from_user.username

    data = await state.get_data()
    currency = data['currency']
    amount = float(data['amount'])

    price_data = await get_price(currency)
    price = float(price_data[0]) * amount
    balance = await get_profile(user_id, username)

    if not balance:
        await state.clear()
        await message.answer("⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.")
        return
    if amount <= 0:
        await state.clear()
        await message.answer("❌ <b>Ошибка</b>\n\nВведите число больше 0")
        return

    
    if currency == "st":
        balance_index = 1
    elif currency == "v":
        balance_index = 2
    else:
        balance_index = 3

    currency_balance = balance[balance_index]

    if data['type'] == 'buy' and data['currency'] == 'box':
        if balance[1] < price:
            await state.clear()
            await message.answer("<b>Недостаточно средств для совершения транзакции!</b>", reply_markup=reply.main)
        else:
            remaining = balance[1] - price
            await message.answer(f"После покупки <b>{amount} 📦</b> на балансе останется <b>{remaining:.2f}ST</b>\n\nПодтвердите покупку кнопками ниже.", reply_markup=inline.agree_buttons)

    elif data['type'] == 'buy':
        if balance[0] < price:
            await state.clear()
            await message.answer("<b>Недостаточно средств для совершения транзакции!</b>", reply_markup=reply.main)
        else:
            remaining = balance[0] - price
            await message.answer(f"После покупки <b>{amount}{currency.upper()}</b> на балансе останется <b>~{remaining:.2f}₽</b>\n\nПодтвердите покупку кнопками ниже.", reply_markup=inline.agree_buttons)
    else:
        if currency_balance < amount:
            await state.clear()
            await message.answer("<b>Недостаточно средств для совершения транзакции!</b>", reply_markup=reply.main)
        else:
            remaining = balance[0] + price
            await message.answer(f"После продажи <b>{amount}{currency.upper()}</b> у вас будет <b>~{remaining:.2f}₽</b>\n\nПодтвердите покупку кнопками ниже.", reply_markup=inline.agree_buttons)

async def open_box(id, username, message: Message, amount: int = 1):
    balance = await get_profile(id, username)

    rarities_icons = {
        'Легендарная': '🟡',
        'Мифическая': '🔴',
        'Эпическая': '🟣',
        'Экзотическая': '🟢',
        'Обычная': '⚪️'
    }

    rarities_order = ['Легендарная', 'Мифическая', 'Эпическая', 'Экзотическая', 'Обычная']

    rarities_chances = {
        'Легендарная': 2,
        'Мифическая': 10,
        'Эпическая': 15,
        'Экзотическая': 27,
        'Обычная': 50
    }

    replay_compensation = {
        'Легендарная': 50,
        'Мифическая': 40,
        'Эпическая': 30,
        'Экзотическая': 20,
        'Обычная': 10
    }

    all_items = await db.select_data("loot", ["id", "name", "rarity"], fetch_all=True)
    res = await db.select_data("users", ["loot"], {"id": id})
    user_loot = json.loads(res['loot']) if res and res['loot'] else []

    if not balance:
        await message.answer(not_register)
        return

    if balance[3] < amount:
        await message.answer(f'⚠️ Недостаточно <b>боксов</b> для открытия. У вас: {balance[3]}, нужно: {amount}.')
        return

    boxes_left = balance[3]
    st_balance = balance[1]
    obtained_items = []
    compensation_total = 0

    for _ in range(amount):
        selected_rarity = random.choices(list(rarities_chances.keys()), weights=rarities_chances.values(), k=1)[0]
        available_items = [item for item in all_items if item[2] == selected_rarity]
        selected_item = random.choice(available_items)
        item_id = selected_item[0]
        item_name = selected_item[1]
        item_rarity = selected_item[2]
        rarity_icon = rarities_icons[item_rarity]

        is_duplicate = any(item['id'] == item_id and item.get('exist', False) for item in user_loot)

        if is_duplicate:
            price = replay_compensation[item_rarity]
            st_balance += price
            compensation_total += price
            obtained_items.append((item_rarity, f"{rarity_icon} <b>{item_name}</b> (повторка +{price}ST)"))
        else:
            user_loot.append({'id': item_id, 'exist': True})
            obtained_items.append((item_rarity, f"{rarity_icon} <b>{item_name}</b>"))

            db.update_data('users', {'loot': json.dumps(user_loot)}, {"id": id})

        # Решаем, тратится ли бокс
        if not is_duplicate and random.randint(0, 1) == 0:
            continue  # Бокс не тратился
        boxes_left -= 1

    # Обновляем финальный баланс
    await db.update_data('users', {'st': st_balance, 'boxes': boxes_left}, {'id': id})

    # Сортировка предметов по редкости
    obtained_items.sort(key=lambda x: rarities_order.index(x[0]))

    # Формирование текста
    items_text = "\n".join(item[1] for item in obtained_items)
    final_text = (
        "<b>Поздравляем!</b>\n"
        "Вы получили:\n"
        f"{items_text}\n\n"
        f"💰 ST: {st_balance} | 📦 Боксы: {boxes_left}"
    )

    if compensation_total > 0:
        final_text += f"\n\n🎁 Компенсация за повторки: +{compensation_total}ST"

    await message.answer(final_text)

async def items(id, username, call, inline):
    rarities_icons = {
        'Легендарная': '🟡',
        'Мифическая': '🔴',
        'Эпическая': '🟣',
        'Экзотическая': '🟢',
        'Обычная': '⚪️'
    }

    rarities_chances = {
        'Легендарная': 2,
        'Мифическая': 10,
        'Эпическая': 15,
        'Экзотическая': 27,
        'Обычная': 50
    }

    all_items = await db.select_data("loot", ["id", "name", "rarity"], fetch_all=True)
    res = await db.select_data("users", ["loot"], {"id": id})
    user_loot = json.loads(res['loot']) if res and res['loot'] else []


    text = ""
    for rarity, chance in rarities_chances.items():
        text += f"<b>{rarities_icons[rarity]} {rarity} ({chance}%):</b> — "
        available_items = [item for item in all_items if item[2] == rarity]
        item_count = len(available_items)
        if user_loot:
            count_with_user = len([item for item in available_items if any(user_item['id'] == item[0] and user_item.get('exist', False) for user_item in user_loot)])
            if count_with_user == 0:
                text += f"0 из {item_count}\n<i>Не открыто ни одного предмета редкости</i>\n"
            else:
                text += f"<b>{count_with_user}</b> из {item_count}\n"
                for item in available_items:
                    if any(user_item['id'] == item[0] and user_item.get('exist', False) for user_item in user_loot):
                        text += f"{item[1]}\n"
        else:
            text += f"0 из {item_count}\n<i>Не открыто ни одного предмета редкости</i>\n"

        text += "\n"  # Добавляем дополнительный перенос строки между редкостями

    return await call.message.edit_text(text, reply_markup=inline.items_buttons)

async def sending(text, bot):
    users = db.select_data('users', ['id'], fetch_all=True)

    # Инициализируем счётчики
    success_count = 0
    error_count = 0

    # Рассылка сообщений
    for user in users:
        user_id = user[0]
        try:
            await bot.send_message(user_id, text)
            success_count += 1
        except Exception:
            error_count += 1

    return f"Успешно отправлено: {success_count}\nНе удалось отправить: {error_count}"