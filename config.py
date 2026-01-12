import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tutormula.db")
    ADMIN_SECRET = os.getenv("ADMIN_SECRET", "supersecret")

settings = Settings()
