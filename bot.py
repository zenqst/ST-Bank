import asyncio
from aiogram import Bot, Dispatcher

from handlers import bot_messages, user_commands
from callbacks import coins

from config_reader import settings

from data.datebase import change_coin
from data.db_init import init_db
from keep_alive import keep_alive

keep_alive()
init_db()

async def scheduled_task(bot: Bot):
    while True:
        await change_coin('st', bot)
        await change_coin('v', bot)
        await asyncio.sleep(300)

async def main():
    bot = Bot(settings.bot_token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher()

    dp.include_routers(
        user_commands.router,
        bot_messages.router,
        coins.router,
    )

    scheduled_task_task = asyncio.create_task(scheduled_task(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await asyncio.gather(scheduled_task_task)


if __name__ == "__main__":
    asyncio.run(main())