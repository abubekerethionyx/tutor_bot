from aiogram.fsm.state import State, StatesGroup

class AttendanceStates(StatesGroup):
    waiting_for_child_pick = State()
    waiting_for_session_pick = State()
    waiting_for_student_selection = State()
    waiting_for_status_pick = State()
