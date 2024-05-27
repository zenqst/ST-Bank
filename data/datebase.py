from psycopg2 import connect
from os import getenv
from dotenv import load_dotenv

import humanize

from config_reader import st, v
from data.google_sheets import add_to_table

import random

from config_reader import config
import json

load_dotenv()

# img = open('data/box_open.gif', 'rb')

dbname = 'postgres'
user = 'postgres.sbcrsartgfmzvwuiyqdr'
host = 'aws-0-eu-central-1.pooler.supabase.com'

not_register = '⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.'

def select_data(rows: list, table: str, identifiers: dict):
    """
    >> select_data(['text'], 'test', {'ids': 5})

    () SELECT text FROM test WHERE ids = %s

    << Тест-тест!
    """

    con = connect(dbname=dbname, user=user, password=getenv('DB_PASSWORD'), host=host)
    cur = con.cursor()

    if identifiers:  # Проверяем, есть ли какие-либо идентификаторы
        identifiers_str = ' AND '.join([f"{key} = %s" for key in identifiers.keys()])
        query = f"SELECT {', '.join(rows)} FROM {table} WHERE {identifiers_str}"
        values = tuple(identifiers.values())
    else:
        query = f"SELECT {', '.join(rows)} FROM {table}"
        values = None

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

    () INSERT INTO test (text, ids) VALUES (%s, %s)
    () Появилась запись Тест-тест!
    """

    con = connect(dbname=dbname, user=user, password=getenv('DB_PASSWORD'), host=host)
    cur = con.cursor() 

    columns = list(values.keys())
    values_list = list(values.values())

    columns_str = ', '.join(columns)
    placeholders = ', '.join(['%s']*len(values_list))
    query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

    cur.execute(query, values_list)
    con.commit()

    cur.close()
    con.close()

def update_data(table: str, values: dict, identifiers: dict):
    """
    >> db_update('test', {'text': 'Тест'}, {'ids': 5})

    () UPDATE test SET text = %s WHERE ids = %s
    () Тест-тест! -> Тест
    """

    con = connect(dbname=dbname, user=user, password=getenv('DB_PASSWORD'), host=host)
    cur = con.cursor()

    set_values_str = ', '.join([f"{key} = %s" for key in values.keys()])
    identifiers_str = ' AND '.join([f"{key} = %s" for key in identifiers.keys()])
    query = f"UPDATE {table} SET {set_values_str} WHERE {identifiers_str}"

    query_values = list(values.values()) + list(identifiers.values())

    cur.execute(query, query_values)
    con.commit()

    cur.close()
    con.close()

def delete_data(table: str, identifiers: dict):
    """
    >> db_delete('test', {'ids': 5})

    () DELETE FROM test WHERE ids = %s
    () Запись удалена
    """

    con = connect(dbname=dbname, user=user, password=getenv('DB_PASSWORD'), host=host)
    cur = con.cursor() 

    identifiers_str = ' AND '.join([f"{key} = %s" for key in identifiers.keys()])
    query = f"DELETE FROM {table} WHERE {identifiers_str}"
    
    values = tuple(identifiers.values())

    cur.execute(query, values)
    con.commit()

    cur.close()
    con.close()

def register(id, username):
    if (select_data(['username'], 'users', {'id': id})):
        return True
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

def buy_coins(id, username, name, pcs: int):
    price = get_price(name)
    price = float(price[0]) * float(pcs)

    balance = get_profile(id, username)

    currency = name.lower()

    if currency == 'st':
        new_balance = balance[1]
    if currency == 'v':
        new_balance = balance[2]

    if price > balance[0]:
        return f'❌ <b>Недостаточно средств</b>\n\nНеобходимо: {price}₽ (Баланс: {balance[0]}₽)'
    if price <= 0:
        return f'❌ <b>Ошибка</b>\n\nВведите число больше 0'
    else:
        update_data('users', {'ruble': balance[0] - price}, {'id': id})
        update_data('users', {currency: new_balance + int(pcs)}, {'id': id})

        return f'✅ <b>Успешно!</b>\n\nВы приобрели <b>{pcs}{name}</b> за <b>{price}₽</b>'
    
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
    
def sell_coins(id, username, name, pcs: int):
    price = get_price(name)
    price = float(price[0]) * float(pcs)

    balance = get_profile(id, username)
    
    currency = name.lower()

    if currency == 'st':
        new_balance = balance[1]
    if currency == 'v':
        new_balance = balance[2]

    if float(pcs) > float(new_balance):
        return f'❌ <b>Недостаточно акций</b>\n\nНеобходимо: {pcs}{name} (Баланс: {new_balance}{name})'
    if price == 0:
        return f'❌ <b>Ошибка</b>\n\nВведите число больше 0'
    else:
        update_data('users', {'ruble': balance[0] + price}, {'id': id})
        update_data('users', {currency: new_balance - int(pcs)}, {'id': id})

        return f'✅ <b>Успешно!</b>\n\nВы продали <b>{pcs}{name}</b> за <b>{price}₽</b>'
    
async def change_coin(name, bot):
    coin = globals()[name.lower()]  # Получаем модуль динамически
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

    # with open('text.txt', 'a') as f:
    #     f.write(f'{name} ({datetime.datetime.now().time()})\nЦена до: {data[0]}\nЦена после: {new_price}\nПроцент: {new_diff_percent}\n\n\n')

    await bot.send_message(config.admin_id, f'{name}\nЦена до: {data[0]}\nЦена после: {new_price}\nПроцент: {new_diff_percent}\n')

    update_data('coins', {'curr_price': new_price, 'diff_percent': new_diff_percent}, {'name': name})

async def advanced_buy(name, state, message, inline):
    await state.update_data(pcs=message.text)
    user_id = message.from_user.id
    username = message.from_user.username

    data = await state.get_data()
    price = get_price(name)
    price = float(price[0]) * float(data['pcs'])
    balance = get_profile(user_id, username)

    buttons = getattr(inline, f'agree_buy_{name.lower()}_buttons')

    if balance:
        await message.answer(f"Для покупки <b>{data['pcs']}{name}</b> потребуется <b>{price}₽</b> (Ваш баланс: <b>{balance[0]}₽</b>)\n\nПодтвердите или отмените покупку кнопками ниже.", reply_markup=buttons)
    else:
        await message.answer('⚠️ Ваш аккаунт <b>не был зарегистрирован</b>. Отправьте команду заново.')

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

async def advanced_sell(name, state, message, inline):
    await state.update_data(pcs=message.text)
    user_id = message.from_user.id
    username = message.from_user.username

    data = await state.get_data()
    price = get_price(name)
    price = float(price[0]) * float(data['pcs'])
    balance = get_profile(user_id, username)

    currency = name.lower()

    if currency == 'st':
        new_balance = balance[1]
    if currency == 'v':
        new_balance = balance[2]

    price += float(balance[0])

    buttons = getattr(inline, f'agree_sell_{name.lower()}_buttons')

    if balance:
        await message.answer(f"После продажи <b>{data['pcs']}{name}</b> у вас будет <b>{price}₽</b> (Текущий баланс: <b>{new_balance}{name}</b>)\n\nПодтвердите или отмените покупку кнопками ниже.", reply_markup=buttons)
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
        'Легендарная': 10000,
        'Мифическая': 5000,
        'Эпическая': 2500,
        'Экзотическая': 1000,
        'Обычная': 500
    }

    con = connect(dbname=dbname, user=user, password=getenv('DB_PASSWORD'), host=host)
    cur = con.cursor()

    query = "SELECT id, name, rarity FROM loot"
    cur.execute(query)
    all_items = cur.fetchall()

    query = "SELECT loot FROM users WHERE id = %s"
    cur.execute(query, (id,))
    user_loot = cur.fetchone()[0]

    if user_loot is None:
        user_loot = []

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

        if any(item['id'] == item_id and item['exist'] for item in user_loot):
            price = replay_compensation[selected_item[2]]
            update_data('users', {'st': balance[1] + price}, {'id': id})
            await message.answer(f"Вы получили <b>{selected_item[1]}</b> <i>({rarity_icon} {selected_item[2]})</i>\nПредмет-повторка: +{price}ST\n\nТекущий баланс: {balance[1] + price}ST и {balance[3] - 1} 📦")
        else:
            user_loot.append({'id': item_id, 'exist': True})

            # Обновляем JSONB-строку в базе данных
            update_query = "UPDATE users SET loot = %s WHERE id = %s"
            cur.execute(update_query, (json.dumps(user_loot), id))
            con.commit()

            refund_box = random.randint(0, 1)

            if refund_box == 0:
                await message.answer(f"<b>Удача на вашей стороне! Бокс не потратился при открытии</b>\nВы получили <b>{selected_item[1]}</b> <i>({rarity_icon} {selected_item[2]})</i>\n\nТекущий баланс: {balance[3]} 📦")
                return

            await message.answer(f"<b>Поздравляем!</b>\nВы получили <b>{selected_item[1]}</b> <i>({rarity_icon} {selected_item[2]})</i>\n\nТекущий баланс: {balance[3] - 1} 📦")
        
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

    con = connect(dbname=dbname, user=user, password=getenv('DB_PASSWORD'), host=host)
    cur = con.cursor()

    query = "SELECT id, name, rarity FROM loot"
    cur.execute(query)
    all_items = cur.fetchall()

    query = "SELECT loot FROM users WHERE id = %s"
    cur.execute(query, (id,))
    user_loot = cur.fetchone()[0]

    text = ""
    for rarity, chance in rarities_chances.items():
        text += f"<b>{rarities_icons[rarity]} {rarity} ({chance}%):</b> — "
        available_items = [item for item in all_items if item[2] == rarity]
        item_count = len(available_items)
        if user_loot:
            count_with_user = len([item for item in available_items if any(user_item['id'] == item[0] and user_item['exist'] for user_item in user_loot)])
            if count_with_user == 0:
                text += f"0 из {item_count}\n<i>Не открыто ни одного предмета редкости</i>\n"
            else:
                text += f"<b>{count_with_user}</b> из {item_count}\n"
                for item in available_items:
                    if any(user_item['id'] == item[0] and user_item['exist'] for user_item in user_loot):
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