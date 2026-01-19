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

def get_main_menu(roles: list[str] = None):
    if roles is None:
        roles = ["student"]
        
    builder = ReplyKeyboardBuilder()
    
    # Common actions
    builder.row(
        types.KeyboardButton(text="Profile"),
        types.KeyboardButton(text="Search Tutors")
    )
    
    # Session Management
    builder.row(
        types.KeyboardButton(text="Create Session"),
        types.KeyboardButton(text="My Sessions")
    )
    
    # Student specific
    if "student" in roles and "tutor" not in roles and "parent" not in roles:
        builder.row(types.KeyboardButton(text="My Attendance"))
    
    # Tutor specific
    if "tutor" in roles:
        builder.row(
            types.KeyboardButton(text="Create Report"),
            types.KeyboardButton(text="My Students")
        )
        
    # Parent specific
    if "parent" in roles:
        builder.row(
            types.KeyboardButton(text="Add New Student"),
            types.KeyboardButton(text="Link Child")
        )
        builder.row(
            types.KeyboardButton(text="My Children"),
            types.KeyboardButton(text="Child Reports")
        )
    
    # Only students can register as parents. Tutors and Parents have their own portals.
    if "parent" not in roles and "student" in roles and "tutor" not in roles:
        builder.row(types.KeyboardButton(text="Register as Parent"))
        
    builder.row(
        types.KeyboardButton(text="Back"),
        types.KeyboardButton(text="Help")
    )
    
    return builder.as_markup(resize_keyboard=True)
