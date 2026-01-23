from aiogram import Bot, Dispatcher
from config import settings
from bot.handlers import common, registration, session, report, parent, attendance
from services.scheduler_service import setup_scheduler

# Initialize Bot and Dispatcher
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

from database.db import engine, Base
from database import models # Ensure models are loaded

def setup_routers():
    """Include routers from different modules"""
    # Ensure tables exist (prevents race conditions or fresh DB crashes)
    Base.metadata.create_all(bind=engine)

    # Priority to common for global buttons like "Back"
    dp.include_router(common.router)
    dp.include_router(registration.router)
    dp.include_router(session.router)
    dp.include_router(report.router)
    dp.include_router(parent.router)
    dp.include_router(attendance.router)

    # Setup Scheduler
    setup_scheduler(bot)
