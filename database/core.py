import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

class DB:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT,
            min_size=1,
            max_size=5
        )

    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None


    from typing import Union

    async def select_data(self, table: str, rows: Union[str, list[str]], identifiers: dict = None, fetch_all: bool = None):
        """
        Получить одну или все строки из таблицы.

        Примеры:
            await db.select_data("users", ["username", "st"], {"id": 12345})
            await db.select_data("users", "*", fetch_all=True)

        :param table: Название таблицы
        :param rows: Поля для выборки (строка или список)
        :param identifiers: Условия WHERE, например: {"id": 123}
        :param fetch_all: True для получения всех строк, False — одной (если не указан, то автоопределение)
        :return: dict | list[dict] | None
        """

        async with self.pool.acquire() as con:
            # Преобразуем строку в список, если нужно
            if isinstance(rows, str) and rows != "*":
                rows = [rows]

            # Генерация SELECT-части
            if rows == "*" or rows == ["*"]:
                row_part = "*"
                fetch_all = True  # Всегда выбираем все строки
            else:
                row_part = ', '.join(rows)

            # Генерация WHERE-части
            if identifiers:
                where_clause = ' AND '.join(f"{k} = ${i+1}" for i, k in enumerate(identifiers.keys()))
                query = f"SELECT {row_part} FROM {table} WHERE {where_clause}"
                values = tuple(identifiers.values())
            else:
                query = f"SELECT {row_part} FROM {table}"
                values = ()

            # Выполняем запрос
            if fetch_all:
                records = await con.fetch(query, *values)
                # Преобразуем список Record в список dict
                return [dict(record) for record in records]
            else:
                record = await con.fetchrow(query, *values)
                # Если результат есть, преобразуем в dict, иначе None
                return dict(record) if record else None



    async def insert_data(self, table: str, values: dict):
        """
        Вставить новую строку в таблицу.

        Пример:
            await db.insert_data("users", {"id": 123, "username": "test"})

        :param table: Название таблицы
        :param values: Пары ключ-значение для вставки
        """

        async with self.pool.acquire() as con:
            columns = ', '.join(values.keys())
            placeholders = ', '.join(f"${i+1}" for i in range(len(values)))
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            await con.execute(query, *values.values())

    async def update_data(self, table: str, values: dict, identifiers: dict):
        """
        Обновить значения в таблице по условию.

        Пример:
            await db.update_data("users", {"st": 100}, {"id": 123})

        :param table: Название таблицы
        :param values: Обновляемые поля
        :param identifiers: WHERE условия
        """

        async with self.pool.acquire() as con:
            set_clause = ', '.join(f"{k} = ${i+1}" for i, k in enumerate(values.keys()))
            where_clause = ' AND '.join(f"{k} = ${i+1+len(values)}" for i, k in enumerate(identifiers.keys()))
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            params = tuple(values.values()) + tuple(identifiers.values())
            await con.execute(query, *params)

    async def delete_data(self, table: str, identifiers: dict):
        """
        Удалить строки из таблицы по условию.

        Пример:
            await db.delete_data("users", {"id": 123})

        :param table: Название таблицы
        :param identifiers: WHERE условия
        """

        async with self.pool.acquire() as con:
            where_clause = ' AND '.join(f"{k} = ${i+1}" for i, k in enumerate(identifiers.keys()))
            query = f"DELETE FROM {table} WHERE {where_clause}"
            values = tuple(identifiers.values())
            await con.execute(query, *values)

db = DB()