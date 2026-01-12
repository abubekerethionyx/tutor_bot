from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import types

def get_role_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Student"),
        types.KeyboardButton(text="Tutor"),
        types.KeyboardButton(text="Parent")
    )
    return builder.as_markup(resize_keyboard=True)

def get_main_menu(role: str = "student"):
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Profile"),
        types.KeyboardButton(text="Search Tutors")
    )
    
    builder.row(
        types.KeyboardButton(text="Create Session"),
        types.KeyboardButton(text="My Sessions")
    )
    
    if role == "tutor":
        builder.row(
            types.KeyboardButton(text="Create Report"),
            types.KeyboardButton(text="My Students")
        )
        
    builder.row(
        types.KeyboardButton(text="Help")
    )
    return builder.as_markup(resize_keyboard=True)
