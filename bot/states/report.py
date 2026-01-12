from aiogram.fsm.state import State, StatesGroup

class ReportStates(StatesGroup):
    waiting_for_session_pick = State()
    waiting_for_content = State()
    waiting_for_score = State()
