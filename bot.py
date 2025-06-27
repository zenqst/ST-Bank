import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import bot_messages, user_commands
from callbacks import coins, donations

from config_reader import settings

from data.queries import change_coin
from data.core import db
from keep_alive import keep_alive

keep_alive()

async def scheduled_task(bot: Bot):
    while True:
        await change_coin('st', bot)
        await change_coin('v', bot)
        await asyncio.sleep(300)

async def main():
    bot = Bot(settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    await db.connect()

    dp.include_routers(
        user_commands.router,
        bot_messages.router,
        coins.router,
        donations.router
    )

    scheduled_task_task = asyncio.create_task(scheduled_task(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await asyncio.gather(scheduled_task_task)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())