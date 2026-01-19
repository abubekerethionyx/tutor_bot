from aiogram.fsm.state import State, StatesGroup

class ParentStates(StatesGroup):
    waiting_for_child_name = State()
    # Adding states for creating a new student directly
    adding_student_name = State()
    adding_student_grade = State()
    adding_student_school = State()
    adding_student_age = State()
