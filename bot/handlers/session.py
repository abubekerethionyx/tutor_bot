from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.states.session import SessionStates
from database.db import SessionLocal
from services.user_service import UserService
from services.session_service import SessionService
from bot.keyboards.common import get_main_menu
from datetime import datetime
from aiogram.utils.keyboard import ReplyKeyboardBuilder

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
    
    from database.models import User
    builder = ReplyKeyboardBuilder()
    
    if is_tutor:
        enrollments = SessionService.get_enrollments_for_tutor(db, user.id)
        if not enrollments:
            await message.answer("You don't have any enrolled students yet.")
            db.close()
            return
        
        for enr in enrollments:
            student = db.query(User).filter(User.id == enr.student_id).first()
            if student:
                builder.button(text=f"Student: {student.full_name} (ID: {student.id})")
        
        prompt = "Which student is this session for?"
    
    elif is_student:
        enrollments = SessionService.get_enrollments_for_student(db, user.id)
        if not enrollments:
            await message.answer("You don't have any enrolled tutors yet. Search and enroll first!")
            db.close()
            return
            
        for enr in enrollments:
            tutor = db.query(User).filter(User.id == enr.tutor_id).first()
            if tutor:
                builder.button(text=f"Tutor: {tutor.full_name} (ID: {tutor.id})")
        
        prompt = "Which tutor is this session for?"
    
    else:
        await message.answer("Only students and tutors can create sessions.")
        db.close()
        return

    builder.adjust(1)
    await message.answer(prompt, reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(SessionStates.waiting_for_student_pick)
    await state.update_data(user_role="tutor" if is_tutor else "student")
    db.close()

@router.message(SessionStates.waiting_for_student_pick)
async def process_student_pick(message: types.Message, state: FSMContext):
    # Extract ID from "Student/Tutor: Name (ID: 123)"
    try:
        other_id = int(message.text.split("ID: ")[1].replace(")", ""))
        await state.update_data(other_id=other_id)
        await message.answer("What is the topic of the session?", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(SessionStates.waiting_for_topic)
    except (IndexError, ValueError):
        await message.answer("Please pick a person from the keyboard.")

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
        user = UserService.get_user_by_telegram_id(db, message.from_user.id)
        
        if data['user_role'] == "tutor":
            tutor_id = user.id
            student_id = data['other_id']
        else:
            tutor_id = data['other_id']
            student_id = user.id

        SessionService.create_session(
            db=db,
            tutor_id=tutor_id,
            student_id=student_id,
            scheduled_at=datetime.fromisoformat(data['scheduled_at']),
            duration_minutes=duration,
            topic=data['topic']
        )
        db.close()
        
        await message.answer("✅ Session created successfully!", reply_markup=get_main_menu(data['user_role']))
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
        from database.models import User
        resp = "👥 *Your Students:*\n\n"
        for enr in enrollments:
            student = db.query(User).filter(User.id == enr.student_id).first()
            if student:
                resp += f"🔹 {student.full_name}\n"
        await message.answer(resp, parse_mode="Markdown")
    db.close()
