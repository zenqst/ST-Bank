from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from dotenv import load_dotenv

import humanize

from config_reader import st, v
from data.google_sheets import add_to_table
from data.db_init import init_db, get_connection
from keyboards import inline, reply

import random

from config_reader import config
import json

load_dotenv()
init_db()

# img = open('data/box_open.gif', 'rb')

not_register = '⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.'

async def select_data(rows: list, table: str, identifiers: dict):
    """
    >> select_data(['text'], 'test', {'ids': 5})

    () SELECT text FROM test WHERE ids = ?
    << Тест-тест!
    """
    con = get_connection()
    cur = con.cursor()

    if identifiers:
        identifiers_str = ' AND '.join([f"{key} = ?" for key in identifiers.keys()])
        query = f"SELECT {', '.join(rows)} FROM {table} WHERE {identifiers_str}"
        values = tuple(identifiers.values())
    else:
        query = f"SELECT {', '.join(rows)} FROM {table}"
        values = ()

    cur.execute(query, values)
    result = cur.fetchone()

    cur.close()
    con.close()

    if result is None:
        return None
    else:
        return result

async def insert_data(table: str, values: dict):
    """
    >> db_insert('test', {'text': 'Тест-тест!', 'ids': 5})

    () INSERT INTO test (text, ids) VALUES (?, ?)
    () Появилась запись Тест-тест!
    """
    con = get_connection()
    cur = con.cursor() 

    columns = list(values.keys())
    values_list = list(values.values())

    columns_str = ', '.join(columns)
    placeholders = ', '.join(['?']*len(values_list))
    query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

    cur.execute(query, values_list)
    con.commit()

    cur.close()
    con.close()

async def update_data(table: str, values: dict, identifiers: dict):
    """
    >> db_update('test', {'text': 'Тест'}, {'ids': 5})

    () UPDATE test SET text = ? WHERE ids = ?
    () Тест-тест! -> Тест
    """
    con = get_connection()
    cur = con.cursor()

    set_values_str = ', '.join([f"{key} = ?" for key in values.keys()])
    identifiers_str = ' AND '.join([f"{key} = ?" for key in identifiers.keys()])
    query = f"UPDATE {table} SET {set_values_str} WHERE {identifiers_str}"

    query_values = list(values.values()) + list(identifiers.values())

    cur.execute(query, query_values)
    con.commit()

    cur.close()
    con.close()


async def delete_data(table: str, identifiers: dict):
    """
    >> db_delete('test', {'ids': 5})

    () DELETE FROM test WHERE ids = ?
    () Запись удалена
    """
    con = get_connection()
    cur = con.cursor() 

    identifiers_str = ' AND '.join([f"{key} = ?" for key in identifiers.keys()])
    query = f"DELETE FROM {table} WHERE {identifiers_str}"
    
    values = tuple(identifiers.values())

    cur.execute(query, values)
    con.commit()

    cur.close()
    con.close()


async def register(id, username):
    if (await select_data(['username'], 'users', {'id': id})):
        return True
    if not username:
        return False
    else:
        await insert_data('users', {'id': id, 'username': username, 'ruble': 2000, 'st': 10, 'v': 5})
        return False
    
async def get_profile(id, username):
    """
    Передаём айди и никнейм
    В ответ получаем формат из: ruble[0], st[1], v[2], boxes[3]
    """

    if (await register(id, username)):
        data = await select_data(['ruble', 'st', 'v', 'boxes'], 'users', {'id': id})
        return data
    else:
        return False

async def get_price(name):
    data = await select_data(['curr_price', 'diff_percent'], 'coins', {'name': name})
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
        await update_data('users', {'st': balance[1] - price}, {'id': id})
        await update_data('users', {'boxes': currency_balance + int(amount)}, {'id': id})
        return f'✅ <b>Успешно!</b>\n\nВы приобрели <b>{amount} 📦</b> за <b>{price}ST</b>'
    elif data['type'] == 'buy':
        if price > balance[0]:
            await state.clear()
            return f'❌ <b>Недостаточно средств</b>\n\nНеобходимо: {price}₽ (Баланс: {balance[0]}₽)'
        await update_data('users', {'ruble': balance[0] - price}, {'id': id})
        await update_data('users', {currency: currency_balance + int(amount)}, {'id': id})
        return f'✅ <b>Успешно!</b>\n\nВы приобрели <b>{amount}{currency.upper()}</b> за <b>{price}₽</b>'
    else:
        if amount > currency_balance:
            await state.clear()
            return f'❌ <b>Недостаточно акций</b>\n\nНеобходимо: {amount}{currency.upper()} (Баланс: {currency_balance}{currency.upper()})'
        await update_data('users', {'ruble': balance[0] + price}, {'id': id})
        await update_data('users', {currency: currency_balance - int(amount)}, {'id': id})
        return f'✅ <b>Успешно!</b>\n\nВы продали <b>{amount}{currency.upper()}</b> за <b>{price}₽</b>'

async def change_coin(name: str, bot: Bot):
    coin = globals()[name]  # Получаем модуль динамически
    max_growth = getattr(coin, 'max_growth')
    max_fall = getattr(coin, 'max_fall')

    random_percent = round(random.uniform(-max_fall, max_growth), 2)

    data = await get_price(name)

    new_price = round(data[0] + data[0] * random_percent, 2)
    new_diff_percent = random_percent * 100

    if float(new_price) <= float(getattr(coin, 'min_price')):
        new_price = float(getattr(coin, 'min_price')) + float(random.randint(0, 100))

    # print(f'{name}\nЦена до: {data[0]}\nЦена после: {new_price}\nПроцент: {new_diff_percent}\n')

    await add_to_table(name, new_price)

    if name == "v":
        await bot.send_message(config.admin_id, f'✅ <b>Цена успешно изменена!</b>')

    await update_data('coins', {'curr_price': new_price, 'diff_percent': new_diff_percent}, {'name': name})

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

    con = get_connection()
    cur = con.cursor()

    query = "SELECT id, name, rarity FROM loot"
    cur.execute(query)
    all_items = cur.fetchall()

    query = "SELECT loot FROM users WHERE id = ?"
    cur.execute(query, (id,))
    res = cur.fetchone()
    user_loot = json.loads(res[0]) if res and res[0] else []

    if not balance:
        await message.answer('⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.')
        cur.close()
        con.close()
        return

    if balance[3] < amount:
        await message.answer(f'⚠️ Недостаточно <b>боксов</b> для открытия. У вас: {balance[3]}, нужно: {amount}.')
        cur.close()
        con.close()
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
            update_query = "UPDATE users SET loot = ? WHERE id = ?"
            cur.execute(update_query, (json.dumps(user_loot), id))
            con.commit()

        # Решаем, тратится ли бокс
        if not is_duplicate and random.randint(0, 1) == 0:
            continue  # Бокс не тратился
        boxes_left -= 1

    # Обновляем финальный баланс
    await update_data('users', {'st': st_balance, 'boxes': boxes_left}, {'id': id})

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

    cur.close()
    con.close()

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

    con = get_connection()
    cur = con.cursor()

    query = "SELECT id, name, rarity FROM loot"
    cur.execute(query)
    all_items = cur.fetchall()

    query = "SELECT loot FROM users WHERE id = ?"
    cur.execute(query, (id,))
    res = cur.fetchone()
    user_loot = json.loads(res[0]) if res and res[0] else []


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

    cur.close()
    con.close()

    return await call.message.edit_text(text, reply_markup=inline.items_buttons)

async def hu_number(number):
    suffix = humanize.intword(number)
    parts = suffix.split()
    if len(parts) == 2:
        return parts[0] + parts[1][0].upper()
    elif len(parts) == 3:
        return parts[0] + parts[2][0].upper()
    return parts[0]

async def sending(text, bot):
    # Подключаемся к базе данных
    con = get_connection()
    cur = con.cursor()

    # Извлекаем всех пользователей из таблицы users
    cur.execute("SELECT id FROM test_users")
    users = cur.fetchall()

    cur.close()
    con.close()

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