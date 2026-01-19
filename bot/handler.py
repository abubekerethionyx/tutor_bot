import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from bot.handlers import common, registration, session, report, parent, attendance
from services.scheduler_service import setup_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Include routers from different modules
    # Priority to common for global buttons like "Back"
    dp.include_router(common.router)
    dp.include_router(registration.router)
    dp.include_router(session.router)
    dp.include_router(report.router)
    dp.include_router(parent.router)
    dp.include_router(attendance.router)

    # Setup Scheduler
    setup_scheduler(bot)

    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
