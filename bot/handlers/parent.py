from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.states.parent import ParentStates
from database.db import SessionLocal
from services.user_service import UserService
from services.session_service import SessionService
from database.models import User, StudentProfile
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.keyboards.common import get_main_menu

router = Router()

@router.message(F.text == "Link Child")
async def link_child_start(message: types.Message, state: FSMContext):
    builder = ReplyKeyboardBuilder()
    builder.button(text="Back")
    await message.answer("Please enter your child's full name (as they registered in the bot):", 
                         reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(ParentStates.waiting_for_child_name)

@router.message(ParentStates.waiting_for_child_name)
async def process_child_name(message: types.Message, state: FSMContext):
    child_name = message.text.strip()
    db = SessionLocal()
    
    # Find child user by name and role student
    from database.models import UserRole
    child = db.query(User).join(UserRole).filter(
        User.full_name.ilike(child_name),
        UserRole.role == "student"
    ).first()
    
    if not child:
        await message.answer("Student not found. 🧐\n\n1. Make sure your child has registered with the bot as a 'Student'.\n2. Ensure the name matches exactly.\n\nYou can also click 'Add New Student' in the main menu for instructions on how to register your child.")
        db.close()
        return
        
    # Get parent
    parent = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    # Link in StudentProfile
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == child.id).first()
    if profile:
        profile.parent_id = parent.id
        db.commit()
        await message.answer(f"✅ Successfully linked to {child.full_name}!", reply_markup=get_main_menu("parent"))
    else:
        await message.answer("Could not find student profile. Please ask them to complete registration.")
        
    db.close()
    await state.clear()

@router.message(F.text == "My Children")
async def my_children_handler(message: types.Message):
    db = SessionLocal()
    parent = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    children = db.query(User).join(StudentProfile, User.id == StudentProfile.user_id).filter(StudentProfile.parent_id == parent.id).all()
    
    if not children:
        await message.answer("You haven't linked any children yet. Use 'Link Child' to begin.")
    else:
        resp = "👶 *Your Registered Children:*\n\n"
        for child in children:
            resp += f"• {child.full_name} (ID: `{child.telegram_id}`)\n"
        await message.answer(resp, parse_mode="Markdown")
    db.close()

@router.message(F.text == "Child Reports")
async def child_reports_handler(message: types.Message):
    db = SessionLocal()
    parent = UserService.get_user_by_telegram_id(db, message.from_user.id)
    children = db.query(User).join(StudentProfile, User.id == StudentProfile.user_id).filter(StudentProfile.parent_id == parent.id).all()
    
    if not children:
        await message.answer("You haven't linked any children yet.")
        db.close()
        return

    # Use a builder to show list of children
    builder = ReplyKeyboardBuilder()
    builder.button(text="Reports for All Children")
    for child in children:
        builder.button(text=f"Reports for {child.full_name}")
    builder.adjust(1)
    builder.button(text="Back")
    
    await message.answer("Select a child to view their reports (or view all):", reply_markup=builder.as_markup(resize_keyboard=True))
    db.close()

@router.message(F.text == "Reports for All Children")
async def show_all_children_reports(message: types.Message):
    db = SessionLocal()
    parent = UserService.get_user_by_telegram_id(db, message.from_user.id)
    children = db.query(User).join(StudentProfile, User.id == StudentProfile.user_id).filter(StudentProfile.parent_id == parent.id).all()
    
    if not children:
        await message.answer("No children linked.")
        db.close()
        return

    resp = "📋 *Consolidated Reports for All Children:*\n\n"
    found_any = False
    
    from database.models import Session as TSession, Report
    for child in children:
        sessions = db.query(TSession).filter(TSession.student_id == child.id).join(Report).order_by(TSession.scheduled_at.desc()).limit(3).all()
        if sessions:
            found_any = True
            resp += f"👤 *{child.full_name}:*\n"
            for sess in sessions:
                resp += f"• {sess.topic} ({sess.scheduled_at.strftime('%m/%d')}): {sess.report.performance_score}/10\n"
            resp += "\n"
    
    if not found_any:
        await message.answer("No recent reports found for any of your children.")
    else:
        await message.answer(resp, parse_mode="Markdown")
    db.close()

@router.message(F.text == "Add New Student")
async def add_new_student_instruction(message: types.Message):
    resp = (
        "🆕 *How to Register a New Student:*\n\n"
        "1. Ask your child to start this bot (@tutorbot2bot).\n"
        "2. They should select *'Student'* and follow the registration steps.\n"
        "3. Once they finish, use the *'Link Child'* button here and type their full name.\n\n"
        "That's it! They will then appear in your portal."
    )
    await message.answer(resp, parse_mode="Markdown")

@router.message(F.text.startswith("Reports for "))
async def show_child_reports(message: types.Message):
    child_name = message.text.replace("Reports for ", "")
    db = SessionLocal()
    parent = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    # Find child by name and parent_id
    child = db.query(User).join(StudentProfile, User.id == StudentProfile.user_id).filter(
        StudentProfile.parent_id == parent.id,
        User.full_name == child_name
    ).first()
    
    if not child:
        await message.answer("Child not found.")
        db.close()
        return
        
    # Get last 5 sessions with reports
    from database.models import Session as TSession, Report
    sessions = db.query(TSession).filter(TSession.student_id == child.id).join(Report).order_by(TSession.scheduled_at.desc()).limit(5).all()
    
    if not sessions:
        await message.answer(f"No reports found for {child_name}.")
    else:
        resp = f"📊 *Recent Reports for {child_name}:*\n\n"
        for sess in sessions:
            resp += f"📅 *{sess.topic}* ({sess.scheduled_at.strftime('%Y-%m-%d')})\n"
            resp += f"⭐ Score: {sess.report.performance_score}/10\n"
            resp += f"📝 {sess.report.content}\n\n"
        await message.answer(resp, parse_mode="Markdown")
    
    db.close()
