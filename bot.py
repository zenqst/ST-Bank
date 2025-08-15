import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from callbacks import admins, common, returns, trade
from config_reader import settings
from database.core import db
from database.currencies import change_all_coins
from database.messages import send_for_admins
from handlers import commands, messages
from keep_alive import keep_alive
from middlewares.antiflood import AntifloodMiddleware
from middlewares.check_user import UserCheckMiddleware

keep_alive()


async def scheduled_task(bot: Bot):
    while True:
        await change_all_coins(bot)


async def on_startup(bot: Bot):
    logging.info("Бот запущен")
    await send_for_admins(bot, "🟢 Бот запущен")


async def on_shutdown(bot: Bot):
    logging.info("Бот остановлен")
    await send_for_admins(bot, "🔴 Бот остановлен")


async def main():
    bot = Bot(
        settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    await db.connect()

    dp.message.middleware(UserCheckMiddleware())
    dp.callback_query.middleware(UserCheckMiddleware())
    dp.message.middleware(AntifloodMiddleware(1))

    dp.include_routers(
        admins.router, commands.router, messages.router, returns.router, trade.router, common.router
    )

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    scheduled_task_task = asyncio.create_task(scheduled_task(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await asyncio.gather(scheduled_task_task)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("choreographer").setLevel(logging.CRITICAL)
    logging.getLogger("kaleido").setLevel(logging.CRITICAL)
    logging.getLogger("plotly").setLevel(logging.CRITICAL)
    logging.getLogger("browser_proc").setLevel(logging.CRITICAL)
    asyncio.run(main())
