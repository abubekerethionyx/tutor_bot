from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.states.report import ReportStates
from database.db import SessionLocal
from services.user_service import UserService
from services.session_service import SessionService
from bot.keyboards.common import get_main_menu
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()

@router.message(F.text == "Create Report")
async def create_report_start(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    if not user or not any(r.role == "tutor" for r in user.roles):
        await message.answer("Only tutors can create reports.")
        db.close()
        return

    # Get recent sessions for this tutor
    sessions = SessionService.get_user_sessions(db, user.id, "tutor")
    if not sessions:
        await message.answer("You have no sessions to report on.")
        db.close()
        return

    builder = ReplyKeyboardBuilder()
    for sess in sessions:
        # Show student name from profile
        student_name = sess.student_profile.full_name if sess.student_profile else "Unknown"
        builder.button(text=f"{sess.topic} with {student_name} (ID: {sess.id})")
    
    builder.adjust(1)
    builder.button(text="Back")
    await message.answer("Which session would you like to report on?", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(ReportStates.waiting_for_session_pick)
    db.close()

@router.message(ReportStates.waiting_for_session_pick)
async def process_session_pick(message: types.Message, state: FSMContext):
    try:
        session_id = int(message.text.split("ID: ")[1].replace(")", ""))
        await state.update_data(session_id=session_id)
        await message.answer("Please provide the report content (summary of progress, etc.):", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(ReportStates.waiting_for_content)
    except (IndexError, ValueError):
        await message.answer("Please pick a session from the keyboard.")

@router.message(ReportStates.waiting_for_content)
async def process_content(message: types.Message, state: FSMContext):
    await state.update_data(content=message.text)
    await message.answer("How would you score the student's performance? (1-10)")
    await state.set_state(ReportStates.waiting_for_score)

@router.message(ReportStates.waiting_for_score)
async def process_score(message: types.Message, state: FSMContext):
    try:
        score = int(message.text)
        if not 1 <= score <= 10:
            await message.answer("Score must be between 1 and 10.")
            return
            
        data = await state.get_data()
        db = SessionLocal()
        user = UserService.get_user_by_telegram_id(db, message.from_user.id)
        
        SessionService.create_report(
            db=db,
            session_id=data['session_id'],
            tutor_id=user.id,
            content=data['content'],
            performance_score=score
        )
        
        # Check and notify parent
        from bot.utils.notifications import check_and_notify_parent
        await check_and_notify_parent(message.bot, data['session_id'], db)
        
        roles = [r.role for r in user.roles]
        db.close()
        
        await message.answer("✅ Report created successfully!", reply_markup=get_main_menu(roles))
        await state.clear()
    except ValueError:
        await message.answer("Please enter a valid number (1-10).")
