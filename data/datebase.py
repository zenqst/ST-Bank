from psycopg2 import connect
from os import getenv
from dotenv import load_dotenv

from config_reader import st, v

import random

from config_reader import config

from openpyxl import load_workbook

load_dotenv()

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

    identifiers_str = ' AND '.join([f"{key} = %s" for key in identifiers.keys()])
    rows_str = ', '.join(rows)
    query = f"SELECT {rows_str} FROM {table} WHERE {identifiers_str}"
    
    values = tuple(identifiers.values())

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
        data = select_data(['ruble', 'st', 'v'], 'users', {'id': id})
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
    if price == 0:
        return f'❌ <b>Ошибка</b>\n\nВведите число больше 0'
    else:
        update_data('users', {'ruble': balance[0] - price}, {'id': id})
        update_data('users', {currency: new_balance + int(pcs)}, {'id': id})

        return f'✅ <b>Успешно!</b>\n\nВы приобрели <b>{pcs}{name}</b> за <b>{price}₽</b>'
    
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
    
