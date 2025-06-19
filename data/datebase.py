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

def select_data(rows: list, table: str, identifiers: dict):
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

def insert_data(table: str, values: dict):
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

def update_data(table: str, values: dict, identifiers: dict):
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


def delete_data(table: str, identifiers: dict):
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


def register(id, username):
    if (select_data(['username'], 'users', {'id': id})):
        return True
    if not username:
        return False
    else:
        insert_data('users', {'id': id, 'username': username, 'ruble': 2000, 'st': 10, 'v': 5})
        return False
    
def get_profile(id, username):
    if (register(id, username)):
        data = select_data(['ruble', 'st', 'v', 'boxes'], 'users', {'id': id})
        return data
    else:
        return False

def get_price(name):
    data = select_data(['curr_price', 'diff_percent'], 'coins', {'name': name})
    return data

async def last_interaction(id: int, username: str, state: FSMContext):
    data = await state.get_data()
    currency = data['currency']
    amount = float(data['amount'])

    price_data = get_price(currency)
    price = float(price_data[0]) * amount

    balance = get_profile(id, username)
    balance_index = 1 if currency == "st" else 2
    currency_balance = balance[balance_index]

    if data['type'] == 'buy':
        if price > balance[0]:
            await state.clear()
            return f'❌ <b>Недостаточно средств</b>\n\nНеобходимо: {price}₽ (Баланс: {balance[0]}₽)'
        update_data('users', {'ruble': balance[0] - price}, {'id': id})
        update_data('users', {currency: currency_balance + int(amount)}, {'id': id})
        return f'✅ <b>Успешно!</b>\n\nВы приобрели <b>{amount}{currency.upper()}</b> за <b>{price}₽</b>'
    else:
        if amount > currency_balance:
            await state.clear()
            return f'❌ <b>Недостаточно акций</b>\n\nНеобходимо: {amount}{currency.upper()} (Баланс: {currency_balance}{currency.upper()})'
        update_data('users', {'ruble': balance[0] + price}, {'id': id})
        update_data('users', {currency: currency_balance - int(amount)}, {'id': id})
        return f'✅ <b>Успешно!</b>\n\nВы продали <b>{amount}{currency.upper()}</b> за <b>{price}₽</b>'

    
def buy_boxes(id, username, pcs: int):
    price = get_price('Box')
    price = float(price[0]) * float(pcs)

    balance = get_profile(id, username)

    if price > balance[1]:
        return f'❌ <b>Недостаточно средств</b>\n\nНеобходимо: {price}ST (Баланс: {balance[1]}ST)'
    if price <= 0:
        return f'❌ <b>Ошибка</b>\n\nВведите число больше 0'
    else:
        update_data('users', {'st': balance[0] - price}, {'id': id})
        update_data('users', {'boxes': balance[3] + int(pcs)}, {'id': id})

        return f'✅ <b>Успешно!</b>\n\nВы приобрели <b>{pcs} 📦</b> за <b>{price}ST</b>'
    
async def change_coin(name: str, bot: Bot):
    coin = globals()[name]  # Получаем модуль динамически
    max_growth = getattr(coin, 'max_growth')
    max_fall = getattr(coin, 'max_fall')

    random_percent = round(random.uniform(-max_fall, max_growth), 2)

    data = get_price(name)

    new_price = round(data[0] + data[0] * random_percent, 2)
    new_diff_percent = random_percent * 100

    if float(new_price) <= float(getattr(coin, 'min_price')):
        new_price = float(getattr(coin, 'min_price')) + float(random.randint(0, 100))

    print(f'{name}\nЦена до: {data[0]}\nЦена после: {new_price}\nПроцент: {new_diff_percent}\n')

    await add_to_table(name, new_price)

    await bot.send_message(config.admin_id, f'{name}\nЦена до: {data[0]}\nЦена после: {new_price}\nПроцент: {new_diff_percent}\n')

    update_data('coins', {'curr_price': new_price, 'diff_percent': new_diff_percent}, {'name': name})

async def advanced_interaction(state: FSMContext, message: Message):
    await state.update_data(amount=message.text)
    user_id = message.from_user.id
    username = message.from_user.username

    data = await state.get_data()
    currency = data['currency']
    amount = float(data['amount'])

    price_data = get_price(currency)
    price = float(price_data[0]) * amount
    balance = get_profile(user_id, username)

    if not balance:
        await state.clear()
        await message.answer("⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.")
        return
    if amount <= 0:
        await state.clear()
        await message.answer("❌ <b>Ошибка</b>\n\nВведите число больше 0")
        return

    balance_index = 1 if currency == "st" else 2
    currency_balance = balance[balance_index]

    if data['type'] == 'buy':
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


async def advanced_buy_boxes(name, state, message, inline):
    await state.update_data(pcs=message.text)
    user_id = message.from_user.id
    username = message.from_user.username

    data = await state.get_data()
    price = get_price(name)
    price = float(price[0]) * float(data['pcs'])
    balance = get_profile(user_id, username)

    if balance:
        await message.answer(f"Для покупки <b>{data['pcs']} 📦</b> потребуется <b>{price}ST</b> (Ваш баланс: <b>{balance[1]}ST</b>)\n\nПодтвердите или отмените покупку кнопками ниже.", reply_markup=inline.agree_buy_box_buttons)
    else:
        await message.answer('⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.')

async def open_box(id, username, message):
    balance = get_profile(id, username)

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
    user_loot = res[0] if res and res[0] else []

    if not balance:
        await message.answer('⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.')
    elif balance[3] < 1:
        await message.answer('⚠️ Недостаточно <b>боксов</b> для открытия.')
    else:
        selected_rarity = random.choices(list(rarities_chances.keys()), weights=rarities_chances.values(), k=1)[0]
        available_items = [item for item in all_items if item[2] == selected_rarity]

        selected_item = random.choice(available_items)
        item_id = selected_item[0]

        rarity_icon = rarities_icons[selected_item[2]]

        if any(item['id'] == item_id and item.get('exist', False) for item in user_loot):
            price = replay_compensation[selected_item[2]]
            update_data('users', {'st': balance[1] + price}, {'id': id})
            await message.answer(
                f"Вы получили <b>{selected_item[1]}</b> <i>({rarity_icon} {selected_item[2]})</i>\n"
                f"Предмет-повторка: +{price}ST\n\nТекущий баланс: {balance[1] + price}ST и {balance[3] - 1} 📦"
            )
        else:
            user_loot.append({'id': item_id, 'exist': True})

            # Обновляем JSONB-строку в базе данных
            update_query = "UPDATE users SET loot = ? WHERE id = ?"
            cur.execute(update_query, (json.dumps(user_loot), id))
            con.commit()

            refund_box = random.randint(0, 1)

            if refund_box == 0:
                await message.answer(
                    f"<b>Удача на вашей стороне! Бокс не потратился при открытии</b>\n"
                    f"Вы получили <b>{selected_item[1]}</b> <i>({rarity_icon} {selected_item[2]})</i>\n\n"
                    f"Текущий баланс: {balance[3]} 📦"
                )
                cur.close()
                con.close()
                return

            await message.answer(
                f"<b>Поздравляем!</b>\n"
                f"Вы получили <b>{selected_item[1]}</b> <i>({rarity_icon} {selected_item[2]})</i>\n\n"
                f"Текущий баланс: {balance[3] - 1} 📦"
            )

        update_data('users', {'boxes': int(balance[3]) - 1}, {'id': id})

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
    user_loot = res[0] if res and res[0] else []

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

def hu_number(number):
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