from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.states.parent import ParentStates
from database.db import SessionLocal
from services.user_service import UserService
from services.session_service import SessionService
from database.models import User, StudentProfile, Session as TSession, Report
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
    
    # Find child profile by name (supporting exact match for security)
    profile = db.query(StudentProfile).filter(StudentProfile.full_name.ilike(child_name)).first()
    
    if not profile:
        await message.answer("Student profile not found. 🧐\n\n1. Make sure your child has registered as a 'Student'.\n2. Ensure the name matches exactly.\n\nYou can also click 'Add New Student' to create a profile for them directly.")
        db.close()
        return
        
    # Get parent user
    parent = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    # Link the parent to this student profile
    profile.parent_id = parent.id
    db.commit()
    
    roles = [r.role for r in parent.roles]
    await message.answer(f"✅ Successfully linked to {profile.full_name}!", reply_markup=get_main_menu(roles))
    db.close()
    await state.clear()

@router.message(F.text == "My Children")
async def my_children_handler(message: types.Message):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    children = UserService.get_managed_children(db, user.id)
    
    if not children:
        await message.answer("You haven't linked any children yet. Use 'Add New Student' to begin.")
    else:
        resp = "👶 *Your Registered Children:*\n\n"
        for child in children:
            status = "Self-managed" if child.user_id else "Managed by you"
            resp += f"• {child.full_name} ({status})\n"
        await message.answer(resp, parse_mode="Markdown")
    db.close()

@router.message(F.text == "Child Reports")
async def child_reports_handler(message: types.Message):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    children = UserService.get_managed_children(db, user.id)
    
    if not children:
        await message.answer("You haven't linked any children yet.")
        db.close()
        return

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
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    children = UserService.get_managed_children(db, user.id)
    
    if not children:
        await message.answer("No children linked.")
        db.close()
        return

    resp = "📋 *Consolidated Reports for All Children:*\n\n"
    found_any = False
    
    for child in children:
        sessions = db.query(TSession).filter(TSession.student_profile_id == child.id).join(Report).order_by(TSession.scheduled_at.desc()).limit(3).all()
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

@router.message(F.text.startswith("Reports for "))
async def show_child_reports(message: types.Message):
    child_name = message.text.replace("Reports for ", "")
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    child = db.query(StudentProfile).filter(
        StudentProfile.parent_id == user.id,
        StudentProfile.full_name == child_name
    ).first()
    
    if not child:
        await message.answer("Child not found.")
        db.close()
        return
        
    sessions = SessionService.get_profile_sessions(db, child.id)
    sessions_with_reports = [s for s in sessions if s.report]
    
    if not sessions_with_reports:
        await message.answer(f"No reports found for {child_name}.")
    else:
        resp = f"📊 *Recent Reports for {child_name}:*\n\n"
        for sess in sessions_with_reports[:5]:
            resp += f"📅 *{sess.topic}* ({sess.scheduled_at.strftime('%Y-%m-%d')})\n"
            resp += f"⭐ Score: {sess.report.performance_score}/10\n"
            resp += f"📝 {sess.report.content}\n\n"
        await message.answer(resp, parse_mode="Markdown")
    
    db.close()

@router.message(F.text == "Add New Student")
async def add_new_student_start(message: types.Message, state: FSMContext):
    await message.answer("Let's register your child. What is their **Full Name**?", 
                         reply_markup=types.ReplyKeyboardRemove(),
                         parse_mode="Markdown")
    await state.set_state(ParentStates.adding_student_name)

@router.message(ParentStates.adding_student_name)
async def process_added_student_name(message: types.Message, state: FSMContext):
    await state.update_data(added_student_name=message.text)
    await message.answer("Which **Grade** is your child in?", parse_mode="Markdown")
    await state.set_state(ParentStates.adding_student_grade)

@router.message(ParentStates.adding_student_grade)
async def process_added_student_grade(message: types.Message, state: FSMContext):
    await state.update_data(added_student_grade=message.text)
    await message.answer("What **School** do they attend?", parse_mode="Markdown")
    await state.set_state(ParentStates.adding_student_school)

@router.message(ParentStates.adding_student_school)
async def process_added_student_school(message: types.Message, state: FSMContext):
    await state.update_data(added_student_school=message.text)
    await message.answer("How **Old** is your child?", parse_mode="Markdown")
    await state.set_state(ParentStates.adding_student_age)

@router.message(ParentStates.adding_student_age)
async def process_added_student_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
    except ValueError:
        await message.answer("Please enter a valid number for age.")
        return

    data = await state.get_data()
    db = SessionLocal()
    parent = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    # Create Student Profile linked to this Parent, but NO NEW USER RECORD
    UserService.create_student_profile(
        db,
        full_name=data['added_student_name'],
        grade=data['added_student_grade'],
        school=data['added_student_school'],
        age=age,
        parent_id=parent.id
    )
    
    roles = [r.role for r in parent.roles]
    await message.answer(f"🎉 Successfully registered and linked {data['added_student_name']} to your account!", 
                         reply_markup=get_main_menu(roles))
    db.close()
    await state.clear()
