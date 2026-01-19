from aiogram.fsm.state import State, StatesGroup

class ParentStates(StatesGroup):
    waiting_for_child_name = State()
