import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from callbacks import common, trade
from config_reader import settings
from database.core import db
from database.queries import change_all_coins
from handlers import commands, messages
from keep_alive import keep_alive
from middlewares.antiflood import AntifloodMiddleware
from middlewares.check_user import UserCheckMiddleware

keep_alive()


async def scheduled_task(bot: Bot):
    while True:
        await change_all_coins(bot)


async def main():
    bot = Bot(settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    await db.connect()

    dp.message.middleware(UserCheckMiddleware())
    dp.callback_query.middleware(UserCheckMiddleware())
    dp.message.middleware(AntifloodMiddleware(2))

    dp.include_routers(
        commands.router,
        messages.router,
        trade.router,
        common.router
    )

    scheduled_task_task = asyncio.create_task(scheduled_task(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await asyncio.gather(scheduled_task_task)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())