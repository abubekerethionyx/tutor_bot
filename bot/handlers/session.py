from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.states.session import SessionStates
from database.db import SessionLocal
from services.user_service import UserService
from services.session_service import SessionService
from bot.keyboards.common import get_main_menu
from datetime import datetime
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database.models import User, StudentProfile

router = Router()

@router.message(F.text == "Create Session")
async def create_session_start(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    if not user:
        await message.answer("Please register first.")
        db.close()
        return

    roles = [r.role for r in user.roles]
    is_tutor = "tutor" in roles
    is_student = "student" in roles
    is_parent = "parent" in roles
    
    builder = ReplyKeyboardBuilder()
    
    if is_tutor:
        enrollments = SessionService.get_enrollments_for_tutor(db, user.id)
        if not enrollments:
            await message.answer("You don't have any enrolled students yet.")
            db.close()
            return
        
        for enr in enrollments:
            profile = db.query(StudentProfile).filter(StudentProfile.id == enr.student_profile_id).first()
            if profile:
                builder.button(text=f"Student Profile: {profile.full_name} (ID: {profile.id})")
        
        prompt = "Which student profile is this session for?"
    
    elif is_student:
        # User is a student, find their own profile
        profile = UserService.get_student_profile(db, user.id)
        if not profile:
            await message.answer("Student profile not found.")
            db.close()
            return
            
        enrollments = SessionService.get_enrollments_for_student_profile(db, profile.id)
        if not enrollments:
            await message.answer("You don't have any enrolled tutors yet. Search and enroll first!")
            db.close()
            return
            
        for enr in enrollments:
            tutor = db.query(User).filter(User.id == enr.tutor_user_id).first()
            if tutor:
                builder.button(text=f"Tutor: {tutor.full_name} (ID: {tutor.id})")
        
        prompt = "Which tutor is this session for?"
        await state.update_data(student_profile_id=profile.id)
    
    elif is_parent:
        children = UserService.get_managed_children(db, user.id)
        if not children:
            await message.answer("You haven't linked any children yet. Link a child first to create sessions for them.")
            db.close()
            return
            
        for child in children:
            builder.button(text=f"For Child Profile: {child.full_name} (ID: {child.id})")
        
        prompt = "Which child profile are you creating this session for?"
        
    else:
        await message.answer("Only students, tutors, and parents can create sessions.")
        db.close()
        return

    builder.adjust(1)
    builder.button(text="Back")
    await message.answer(prompt, reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(SessionStates.waiting_for_student_pick)
    
    role_flag = "tutor" if is_tutor else ("student" if is_student else "parent")
    await state.update_data(user_role=role_flag)
    db.close()

@router.message(SessionStates.waiting_for_student_pick)
async def process_student_pick(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db = SessionLocal()
    
    if message.text.startswith("For Child Profile:"):
        try:
            profile_id = int(message.text.split("ID: ")[1].replace(")", ""))
            enrollments = SessionService.get_enrollments_for_student_profile(db, profile_id)
            
            if not enrollments:
                await message.answer("This child has no enrolled tutors. Please enroll them first.")
                db.close()
                return
                
            builder = ReplyKeyboardBuilder()
            for enr in enrollments:
                tutor = db.query(User).filter(User.id == enr.tutor_user_id).first()
                if tutor:
                    builder.button(text=f"Tutor: {tutor.full_name} (ID: {tutor.id})")
            
            builder.adjust(1)
            builder.button(text="Back")
            await message.answer("Which tutor is this session with?", reply_markup=builder.as_markup(resize_keyboard=True))
            await state.update_data(student_profile_id=profile_id)
            db.close()
            return
        except (IndexError, ValueError):
            await message.answer("Please pick a profile from the keyboard.")
            db.close()
            return

    # Standard flow for tutors/students
    try:
        other_id = int(message.text.split("ID: ")[1].replace(")", ""))
        
        if data['user_role'] == "tutor":
            await state.update_data(student_profile_id=other_id, tutor_id=UserService.get_user_by_telegram_id(db, message.from_user.id).id)
        elif data['user_role'] == "student":
            await state.update_data(tutor_id=other_id)
            # student_profile_id already set in create_session_start
        elif data['user_role'] == "parent":
            await state.update_data(tutor_id=other_id)
            
        await message.answer("What is the topic of the session?", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(SessionStates.waiting_for_topic)
    except (IndexError, ValueError):
        await message.answer("Please pick a person from the keyboard.")
    db.close()

@router.message(SessionStates.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await message.answer("When is the session? (Use YYYY-MM-DD HH:MM format, e.g., 2024-05-20 15:30)")
    await state.set_state(SessionStates.waiting_for_date)

@router.message(SessionStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        scheduled_at = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        await state.update_data(scheduled_at=scheduled_at.isoformat())
        await message.answer("How many minutes will the session last?")
        await state.set_state(SessionStates.waiting_for_duration)
    except ValueError:
        await message.answer("Invalid format. Please use YYYY-MM-DD HH:MM")

@router.message(SessionStates.waiting_for_duration)
async def process_duration(message: types.Message, state: FSMContext):
    try:
        duration = int(message.text)
        data = await state.get_data()
        
        db = SessionLocal()
        
        tutor_id = data.get('tutor_id')
        student_profile_id = data.get('student_profile_id')

        SessionService.create_session(
            db=db,
            tutor_id=tutor_id,
            student_profile_id=student_profile_id,
            scheduled_at=datetime.fromisoformat(data['scheduled_at']),
            duration_minutes=duration,
            topic=data['topic']
        )
        db.close()
        
        user = UserService.get_user_by_telegram_id(SessionLocal(), message.from_user.id)
        roles = [r.role for r in user.roles]
        await message.answer("✅ Session created successfully!", reply_markup=get_main_menu(roles))
        await state.clear()
    except ValueError:
        await message.answer("Please enter a valid number of minutes.")

@router.message(F.text == "My Students")
async def my_students_handler(message: types.Message):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    if not user:
        db.close()
        return

    enrollments = SessionService.get_enrollments_for_tutor(db, user.id)
    if not enrollments:
        await message.answer("You have no enrolled students.")
    else:
        resp = "👥 *Your Students (by Profile):*\n\n"
        for enr in enrollments:
            profile = db.query(StudentProfile).filter(StudentProfile.id == enr.student_profile_id).first()
            if profile:
                resp += f"🔹 {profile.full_name} (Grade {profile.grade})\n"
        await message.answer(resp, parse_mode="Markdown")
    db.close()
