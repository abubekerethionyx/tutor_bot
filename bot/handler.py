import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from bot.handlers import common, registration, session, report, parent, attendance
from services.scheduler_service import setup_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)

from bot.loader import bot, dp, setup_routers

async def main():
    # Setup routers and scheduler
    setup_routers()

    print("Bot is starting...")
    # Fix for TelegramConflictError: If a webhook was set (e.g. by the deployed app),
    # we must delete it before we can use polling locally.
    await bot.delete_webhook(drop_pending_updates=True) 
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
