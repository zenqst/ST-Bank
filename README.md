
# ST Bank

[![CodeFactor](https://www.codefactor.io/repository/github/zenqst/st-bank/badge)](https://www.codefactor.io/repository/github/zenqst/st-bank)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/d07e3d49cbf24455862e4b80184e5f67)](https://app.codacy.com/gh/zenqst/ST-Bank/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Python](https://img.shields.io/badge/language-Python-blue.svg)](https://github.com/zenqst/ST-Bank)
[![Last Commit](https://img.shields.io/github/last-commit/zenqst/ST-Bank.svg)](https://github.com/zenqst/ST-Bank/commits/dev)
[![Repo Size](https://img.shields.io/github/repo-size/zenqst/ST-Bank.svg)](https://github.com/zenqst/ST-Bank)
[![Issues](https://img.shields.io/github/issues/zenqst/ST-Bank.svg)](https://github.com/zenqst/ST-Bank/issues)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

---

**ST Bank** is a Telegram-based virtual economy bot written in Python. It features coin trading, dynamic pricing, and user inventory management backed by PostgreSQL.

---

## 🚀 Features

- User registration with initial balances
- Coin trading system (`ST`, `V`)
- Dynamic coin price updates with random growth or decline
- Purchase of boxes (inventory items)
- Profile view with real-time balances
- Telegram bot interaction for all commands

---

## 🛠️ Tech Stack

- **Language:** Python 3.11+
- **Database:** PostgreSQL (via `asyncpg`)
- **Bot Framework:** `aiogram`
- **Other Tools:** `python-dotenv`, `PrettyTable`, `aiohttp`, `pydentic`, `uv`, `ruff`

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/zenqst/ST-Bank.git
cd ST-Bank
```

### 2. Install dependencies

```bash
uv install
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
BOT_TOKEN=YOUR_TOKEN
DB_PORT=YOUR_PORT
DB_USER=YOUR_USER
DB_PASSWORD=YOUR_PASS
DB_NAME=YOUR_NAME
DB_HOST=YOUR_HOST
DB_POOL_MIN=1
DB_POOL_MAX=5
NOTIFY_CHAT_ID=YOUR_ID
GITHUB_TOKEN=YOUR_TOKEN
GITHUB_REPO=USERNAME/REPO
GITHUB_REF=REF
SERVER_IP=YOURIP
SERVER_USERNAME=YOUR_USERNAME
SERVER_PASSWORD=YOUR_PASSWORD
```

### 4. Run the bot

```bash
uv run bot.py
```

----------

## 🗂️ Project Structure

```
ST-Bank/
├── .env
├── README.md
├── bot.py
├── config_reader.py
├── keep_alive.py
├── uv.lock
├── pyproject.toml
├── callbacks/
│   ├── admins.py
│   ├── common.py
│   ├── returns.py
│   └── trade.py
├── database/
│   ├── core.py
│   ├── currencies.py
│   ├── loot.py
│   ├── stats.py
│   ├── messages.py
│   └── utils.py
├── handlers/
│   ├── commands.py
│   └── messages.py
├── keyboards/
│   ├── builders.py
│   ├── inline.py
│   └── reply.py
├── middlewares/
│   ├── antiflood.py
│   └── check_user.py
├── states/
│   ├── enums.py
│   ├── types.py
│   └── fsm_states.py
├── tests/
│   └── test_stats.py
└── utils/
```

----------

## 📄 Documentation

-   User commands via Telegram bot
-   Business logic in `database/`
-   Coin model and price flow
-   Integration setup for Google Sheets
-   Environment configuration via `.env`
    

----------

## 🤝 Contributing

I welcome contributions. Please follow these steps:

1.  Fork the repository
2.  Create a new branch (`git checkout -b feature/my-feature`)
3.  Commit your changes
4.  Push to your fork (`git push origin feature/my-feature`)
5.  Open a Pull Request
    

----------

## 📧 Contact

- Maintainer: [@zenqst](https://github.com/zenqst])
- Issues: Please use the [GitHub Issue Tracker](https://github.com/zenqst/ST-Bank/issues)
- Bot: [@ST_Bank_bot](https://t.me/ST_Bank_bot])
    

----------

## 📝 License

This project is licensed under the MIT License.