import sqlite3
import os
import json
from pathlib import Path

DB_PATH = 'data/database.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    con = get_connection()
    cur = con.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        ruble REAL DEFAULT 2000,
        st REAL DEFAULT 10,
        v REAL DEFAULT 5,
        boxes INTEGER DEFAULT 0,
        loot TEXT DEFAULT '[]'
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS coins (
        name TEXT PRIMARY KEY,
        curr_price REAL,
        diff_percent REAL
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS loot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rarity TEXT CHECK (rarity IN ('Обычная', 'Экзотическая', 'Эпическая', 'Мифическая', 'Легендарная'))
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS test_users (
        id INTEGER PRIMARY KEY
    )
    ''')

    con.commit()
    con.close()