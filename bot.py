import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import commands, messages
from middlewares.check_user import UserCheckMiddleware

from config_reader import settings

from database.core import db
from keep_alive import keep_alive

keep_alive()

async def scheduled_task(bot: Bot):
    while True:
        # TODO: Изменение цены валюты
        pass
        # await change_coin('st', bot)
        # await change_coin('v', bot)
        # await asyncio.sleep(300)

async def main():
    bot = Bot(settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    await db.connect()

    dp.message.middleware(UserCheckMiddleware())
    dp.callback_query.middleware(UserCheckMiddleware())

    dp.include_routers(
        commands.router,
        messages.router
    )

    # scheduled_task_task = asyncio.create_task(scheduled_task(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    # await asyncio.gather(scheduled_task_task)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())