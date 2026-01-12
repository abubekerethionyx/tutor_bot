from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_role = State()
    waiting_for_full_name = State()
    waiting_for_phone = State()
    
    # Student specific
    waiting_for_grade = State()
    waiting_for_school = State()
    waiting_for_age = State()
    
    # Tutor specific
    waiting_for_subjects = State()
    waiting_for_education = State()
    waiting_for_experience = State()
    
    # Parent specific
    waiting_for_occupation = State()
