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
    builder.row(
        types.KeyboardButton(text="Profile"),
        types.KeyboardButton(text="Search Tutors")
    )
    
    builder.row(
        types.KeyboardButton(text="Create Session"),
        types.KeyboardButton(text="My Sessions")
    )
    
    if "tutor" in roles:
        builder.row(
            types.KeyboardButton(text="Create Report"),
            types.KeyboardButton(text="My Students")
        )
    if "parent" in roles:
        builder.row(
            types.KeyboardButton(text="Link Child"),
            types.KeyboardButton(text="My Children")
        )
        builder.row(
            types.KeyboardButton(text="Child Reports")
        )
        builder.row(
            types.KeyboardButton(text="Add New Student")
        )
    
    # Allow adding missing roles (only if not a parent or explicitly requested)
    if "parent" not in roles:
        all_roles = ["student", "tutor", "parent"]
        for r in all_roles:
            if r not in roles:
                builder.row(types.KeyboardButton(text=f"Register as {r.capitalize()}"))
        
    builder.row(types.KeyboardButton(text="Back"))
    builder.row(types.KeyboardButton(text="Help"))
    
    return builder.as_markup(resize_keyboard=True)
