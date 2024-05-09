import asyncio
from aiogram import Bot, Dispatcher

from handlers import bot_messages, user_commands, questionaire
from callbacks import coins

from config_reader import settings

from data.datebase import change_coin
from keep_alive import keep_alive

keep_alive()

async def scheduled_task(bot: Bot):
    while True:
        await change_coin('ST', bot)
        await change_coin('V', bot)
        await asyncio.sleep(30)

async def main():
    bot = Bot(settings.bot_token.get_secret_value(), parse_mode="HTML")
    dp = Dispatcher()

    dp.include_routers(
        user_commands.router,
        questionaire.router,
        bot_messages.router,
        coins.router,
    )

    scheduled_task_task = asyncio.create_task(scheduled_task(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await asyncio.gather(scheduled_task_task)


if __name__ == "__main__":
    asyncio.run(main())