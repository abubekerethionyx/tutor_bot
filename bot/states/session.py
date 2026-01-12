from aiogram.fsm.state import State, StatesGroup

class SessionStates(StatesGroup):
    waiting_for_student_pick = State()
    waiting_for_topic = State()
    waiting_for_date = State()
    waiting_for_duration = State()
