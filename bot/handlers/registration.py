from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.states.registration import RegistrationStates
from database.db import SessionLocal
from services.user_service import UserService
from bot.keyboards.common import get_main_menu

router = Router()

@router.message(RegistrationStates.waiting_for_role)
async def process_role(message: types.Message, state: FSMContext):
    role = message.text.lower()
    if role not in ["student", "tutor", "parent"]:
        await message.answer("Please choose one of the roles: Student, Tutor, or Parent.")
        return

    await state.update_data(role=role)
    await message.answer("Great! What is your full name?", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(RegistrationStates.waiting_for_full_name)

@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Thank you. What is your phone number?")
    await state.set_state(RegistrationStates.waiting_for_phone)

@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    data = await state.get_data()
    role = data['role']

    if role == "student":
        await message.answer("Which grade are you in?")
        await state.set_state(RegistrationStates.waiting_for_grade)
    elif role == "tutor":
        await message.answer("Which subjects do you teach?")
        await state.set_state(RegistrationStates.waiting_for_subjects)
    elif role == "parent":
        await message.answer("What is your occupation?")
        await state.set_state(RegistrationStates.waiting_for_occupation)

# --- Student Flow ---
@router.message(RegistrationStates.waiting_for_grade)
async def process_grade(message: types.Message, state: FSMContext):
    await state.update_data(grade=message.text)
    await message.answer("What school do you attend?")
    await state.set_state(RegistrationStates.waiting_for_school)

@router.message(RegistrationStates.waiting_for_school)
async def process_school(message: types.Message, state: FSMContext):
    await state.update_data(school=message.text)
    await message.answer("How old are you?")
    await state.set_state(RegistrationStates.waiting_for_age)

@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age_val = int(message.text)
    except ValueError:
        await message.answer("Please enter a valid number for age.")
        return
        
    await state.update_data(age=age_val)
    await finish_registration(message, state)

# --- Tutor Flow ---
@router.message(RegistrationStates.waiting_for_subjects)
async def process_subjects(message: types.Message, state: FSMContext):
    await state.update_data(subjects=message.text)
    await message.answer("What is your educational background?")
    await state.set_state(RegistrationStates.waiting_for_education)

@router.message(RegistrationStates.waiting_for_education)
async def process_education(message: types.Message, state: FSMContext):
    await state.update_data(education=message.text)
    await message.answer("How many years of experience do you have?")
    await state.set_state(RegistrationStates.waiting_for_experience)

@router.message(RegistrationStates.waiting_for_experience)
async def process_experience(message: types.Message, state: FSMContext):
    try:
        exp_val = int(message.text)
    except ValueError:
        await message.answer("Please enter a valid number for experience.")
        return
    await state.update_data(experience_years=exp_val)
    await finish_registration(message, state)

# --- Parent Flow ---
@router.message(RegistrationStates.waiting_for_occupation)
async def process_occupation(message: types.Message, state: FSMContext):
    await state.update_data(occupation=message.text)
    await finish_registration(message, state)

async def finish_registration(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db = SessionLocal()
    
    # Create User
    user = UserService.create_user(
        db, 
        telegram_id=message.from_user.id, 
        full_name=data['full_name'],
        phone=data['phone']
    )
    
    # Assign Role
    UserService.assign_role(db, user.id, data['role'])
    
    # Create Profile
    if data['role'] == "student":
        UserService.create_student_profile(
            db, 
            user_id=user.id, 
            full_name=user.full_name,
            grade=data['grade'], 
            school=data['school'], 
            age=data['age']
        )
    elif data['role'] == "tutor":
        UserService.create_tutor_profile(
            db, user.id, data['subjects'], data['education'], data['experience_years']
        )
    elif data['role'] == "parent":
        UserService.create_parent_profile(db, user.id, data['occupation'])

    db.refresh(user)
    roles = [r.role for r in user.roles]
    db.close()
    await state.clear()
    await message.answer(
        "Registration complete! 🎉 You can now use the menu below.",
        reply_markup=get_main_menu(roles)
    )
