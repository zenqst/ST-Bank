import asyncpg
import os
from dotenv import load_dotenv
import logging
import re
from typing import Union

from states.enums import StatusMessages

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", 1))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", 5))

# checking for important vars
required_env_vars = ["DB_USER", "DB_PASSWORD", "DB_NAME", "DB_HOST", "DB_PORT"]
for var in required_env_vars:
    if os.getenv(var) is None:
        raise RuntimeError(f"Environment variable {var} not installed")

ALLOWED_TABLES = {"users", "items", "coins"}

def safe_identifier(identifier: str) -> str:
    """
    Проверяет, что идентификатор (имя таблицы/поля) безопасен для вставки в SQL.
    Разрешены только латинские буквы, цифры и подчёркивание.
    """
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", identifier):
        raise ValueError(f"Invalid name: {identifier}")
    return identifier

class DB:
    def __init__(self):
        self.pool: Union[asyncpg.Pool, None] = None

    async def connect(self):
        """
        Создание пула соединий с бд
        """
        self.pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT,
            min_size=DB_POOL_MIN,
            max_size=DB_POOL_MAX
        )
        logging.info("Successful connection to DB")

    async def close(self):
        """
        Закрытие пула соединий с бд
        """
        if self.pool:
            await self.pool.close()
            self.pool = None
            logging.info("The pool of connections is closed")

    async def select_data(self, table: str, rows: Union[str, list[str]], identifiers: dict = None, fetch_all: bool = None):
        """
        Функция для получения одной или нескольких строк из бд

        Примеры:
            await db.select_data("users", ["username", "st"], {"id": 12345})
            await db.select_data("users", "*", fetch_all=True)

        :param table: Название таблицы
        :param rows: Поля для выборки (строка или список)
        :param identifiers: Условия WHERE, например: {"id": 123}
        :param fetch_all: True для получения всех строк, False — одной (если не указан, то автоопределение)
        :return: dict | list[dict] | None
        """
        safe_identifier(table)
        if table not in ALLOWED_TABLES:
            raise ValueError(StatusMessages.TABLE_DENIED)

        if isinstance(rows, str) and rows != "*":
            rows = [rows]

        if rows == "*" or rows == ["*"]:
            row_part = "*"
            fetch_all = True
        else:
            row_part = ', '.join(safe_identifier(col) for col in rows)

        try:
            async with self.pool.acquire() as con:
                if identifiers:
                    where_clause = ' AND '.join(f"{safe_identifier(k)} = ${i+1}" for i, k in enumerate(identifiers.keys()))
                    query = f"SELECT {row_part} FROM {table} WHERE {where_clause}"
                    values = tuple(identifiers.values())
                else:
                    query = f"SELECT {row_part} FROM {table}"
                    values = ()

                if fetch_all:
                    records = await con.fetch(query, *values)
                    return [dict(record) for record in records]
                else:
                    record = await con.fetchrow(query, *values)
                    return dict(record) if record else None
        except Exception:
            logging.exception(StatusMessages.REQUEST_ERROR)
            raise

    async def insert_data(self, table: str, values: dict):
        """
        Функция для вставления новых строк в таблицу

        Пример:
            await db.insert_data("users", {"id": 123, "username": "test"})

        :param table: Название таблицы
        :param values: Пары ключ-значение для вставки
        """
        safe_identifier(table)
        if table not in ALLOWED_TABLES:
            raise ValueError(StatusMessages.TABLE_DENIED)

        try:
            async with self.pool.acquire() as con:
                columns = ', '.join(safe_identifier(k) for k in values.keys())
                placeholders = ', '.join(f"${i+1}" for i in range(len(values)))
                query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                await con.execute(query, *values.values())
        except Exception:
            logging.exception(StatusMessages.REQUEST_ERROR)
            raise

    async def update_data(self, table: str, values: dict, identifiers: dict):
        """
        Функция для обновления строчек в бд

        Пример:
            await db.update_data("users", {"st": 100}, {"id": 123})

        :param table: Название таблицы
        :param values: Обновляемые поля
        :param identifiers: WHERE условия
        """
        safe_identifier(table)
        if table not in ALLOWED_TABLES:
            raise ValueError(StatusMessages.TABLE_DENIED)

        if not identifiers:
            raise ValueError(StatusMessages.REQUEST_WITHOUT)

        try:
            async with self.pool.acquire() as con:
                set_clause = ', '.join(f"{safe_identifier(k)} = ${i+1}" for i, k in enumerate(values.keys()))
                where_clause = ' AND '.join(f"{safe_identifier(k)} = ${i+1+len(values)}" for i, k in enumerate(identifiers.keys()))
                query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
                params = tuple(values.values()) + tuple(identifiers.values())
                await con.execute(query, *params)
        except Exception:
            logging.exception(StatusMessages.REQUEST_ERROR)
            raise

    async def delete_data(self, table: str, identifiers: dict):
        """
        Функция для удаления строк из таблицы

        Пример:
            await db.delete_data("users", {"id": 123})

        :param table: Название таблицы
        :param identifiers: WHERE условия
        """
        safe_identifier(table)
        if table not in ALLOWED_TABLES:
            raise ValueError(StatusMessages.TABLE_DENIED)

        if not identifiers:
            raise ValueError(StatusMessages.REQUEST_WITHOUT)

        try:
            async with self.pool.acquire() as con:
                where_clause = ' AND '.join(f"{safe_identifier(k)} = ${i+1}" for i, k in enumerate(identifiers.keys()))
                query = f"DELETE FROM {table} WHERE {where_clause}"
                values = tuple(identifiers.values())
                await con.execute(query, *values)
        except Exception:
            logging.exception(StatusMessages.REQUEST_ERROR)
            raise

db = DB()
