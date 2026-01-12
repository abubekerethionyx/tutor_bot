import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from bot.handlers import common, registration, session, report

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Include routers from different modules
    dp.include_router(registration.router)
    dp.include_router(session.router)
    dp.include_router(report.router)
    dp.include_router(common.router)

    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
