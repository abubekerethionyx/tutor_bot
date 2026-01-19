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

    if not any(r.role == "tutor" for r in user.roles):
        await message.answer("Only tutors can create sessions.")
        db.close()
        return

    builder = ReplyKeyboardBuilder()
    
    enrollments = SessionService.get_enrollments_for_tutor(db, user.id)
    if not enrollments:
        await message.answer("You don't have any enrolled students yet.")
        db.close()
        return
    
    await state.update_data(user_role="tutor", enrollments=[(enr.student_profile_id, db.query(StudentProfile).filter(StudentProfile.id == enr.student_profile_id).first().full_name) for enr in enrollments], selected_ids=[])
    
    # Show selection menu
    await show_student_selection_menu(message, state)
    db.close()

async def show_student_selection_menu(message: types.Message, state: FSMContext):
    data = await state.get_data()
    enrollments = data.get('enrollments', [])
    selected_ids = data.get('selected_ids', [])
    
    builder = ReplyKeyboardBuilder()
    
    for pid, name in enrollments:
        status = "✅" if pid in selected_ids else "⬜"
        builder.button(text=f"{status} {name} (ID: {pid})")
    
    builder.adjust(1)
    builder.button(text="Done")
    builder.button(text="Back")
    
    if hasattr(message, 'reply_markup'):
         # If called from button click, it is different but here we use ReplyKeyboard so we always send new message or just update?
         # ReplyKeyboard can't be edited in place easily like Inline.
         # So we just send a new message "Select students:"
         pass
         
    await message.answer("Select students for the session (Toggle):", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(SessionStates.waiting_for_student_pick)

@router.message(SessionStates.waiting_for_student_pick)
async def process_student_pick(message: types.Message, state: FSMContext):
    data = await state.get_data()
    selected_ids = data.get('selected_ids', [])
    
    if message.text == "Back":
        await message.answer("Main Menu", reply_markup=get_main_menu(["tutor"])) 
        await state.clear()
        return

    if message.text == "Done":
        if not selected_ids:
            await message.answer("Please select at least one student.")
            return
            
        await message.answer("What is the topic of the session?", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(SessionStates.waiting_for_topic)
        return

    try:
        # Expected format: "✅ Name (ID: 123)" or "⬜ Name (ID: 123)"
        other_id = int(message.text.split("ID: ")[1].replace(")", ""))
        
        if other_id in selected_ids:
            selected_ids.remove(other_id)
        else:
            selected_ids.append(other_id)
        
        await state.update_data(selected_ids=selected_ids)
        await show_student_selection_menu(message, state) # Refresh menu
        
    except (IndexError, ValueError, AttributeError):
        await message.answer("Please use the keyboard buttons.")

@router.message(F.text == "My Sessions")
async def my_sessions_handler(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    if not user:
        await message.answer("Please register first.")
        db.close()
        return

    roles = [r.role for r in user.roles]
    is_tutor = "tutor" in roles
    is_parent = "parent" in roles
    is_student = "student" in roles

    # Parent/Tutor must select student
    if is_parent or is_tutor:
        builder = ReplyKeyboardBuilder()
        
        if is_parent:
            profiles = UserService.get_managed_children(db, user.id)
            prompt = "Select a child to view sessions for:"
            label_prefix = "Child"
        else: # is_tutor
            enrollments = SessionService.get_enrollments_for_tutor(db, user.id)
            profiles = []
            seen_ids = set()
            for enr in enrollments:
                if enr.student_profile_id not in seen_ids:
                    p = db.query(StudentProfile).filter(StudentProfile.id == enr.student_profile_id).first()
                    if p:
                        profiles.append(p)
                        seen_ids.add(p.id)
            prompt = "Select a student to view sessions for:"
            label_prefix = "Student"

        if not profiles:
            entity = "children" if is_parent else "students"
            await message.answer(f"You have no linked {entity}.")
            db.close()
            return

        for p in profiles:
            builder.button(text=f"{label_prefix}: {p.full_name} (ID: {p.id})")
        
        builder.adjust(1)
        builder.button(text="Back")
        
        await message.answer(prompt, reply_markup=builder.as_markup(resize_keyboard=True))
        await state.set_state(SessionStates.waiting_for_student_filter)
        await state.update_data(session_filter_role="parent" if is_parent else "tutor")
        db.close()
        return

    # Student: View own sessions without selection
    if is_student:
        sessions = SessionService.get_user_sessions(db, user.id, "student")
        if not sessions:
            await message.answer("You have no upcoming sessions.")
        else:
            response = "📅 *Your Sessions:*\n\n"
            for sess in sessions:
                tutor = db.query(User).filter(User.id == sess.tutor_id).first()
                with_name = tutor.full_name if tutor else "Unknown"
                response += (
                    f"🔹 *{sess.topic}*\n"
                    f"👤 Tutor: {with_name}\n"
                    f"⏰ {sess.scheduled_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"⏳ {sess.duration_minutes} min\n\n"
                )
            await message.answer(response, parse_mode='Markdown')
        db.close()
        return

    await message.answer("Unknown role.")
    db.close()

@router.message(SessionStates.waiting_for_student_filter)
async def process_student_filter(message: types.Message, state: FSMContext):
    if message.text == "Back":
        await state.clear()
        # Need user to pass roles to get_main_menu, re-fetch user
        db = SessionLocal()
        user = UserService.get_user_by_telegram_id(db, message.from_user.id)
        roles = [r.role for r in user.roles] if user else []
        db.close()
        await message.answer("Main Menu", reply_markup=get_main_menu(roles))
        return

    try:
        # Format: "Child: Name (ID: 123)" or "Student: Name (ID: 123)"
        profile_id = int(message.text.split("ID: ")[1].replace(")", ""))
        
        db = SessionLocal()
        
        # Verify ownership/access?
        # Assuming ID from sticky keyboard is valid for now
        
        sessions = SessionService.get_profile_sessions(db, profile_id)
        
        profile = db.query(StudentProfile).filter(StudentProfile.id == profile_id).first()
        name = profile.full_name if profile else "Student"
        
        if not sessions:
            await message.answer(f"📅 No sessions found for {name}.")
        else:
            response = f"📅 *Sessions for {name}:*\n\n"
            for sess in sessions:
                tutor = db.query(User).filter(User.id == sess.tutor_id).first()
                tutor_name = tutor.full_name if tutor else "Unknown"
                
                response += (
                    f"🔹 *{sess.topic}*\n"
                    f"👤 Tutor: {tutor_name}\n"
                    f"⏰ {sess.scheduled_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"⏳ {sess.duration_minutes} min\n\n"
                )
            await message.answer(response, parse_mode="Markdown")
            
        # Don't clear state if we want better navigation? Or clear and return to menu?
        # Typically clear state after showing result.
        
        await state.clear()
        # Return to main menu
        user = UserService.get_user_by_telegram_id(db, message.from_user.id)
        roles = [r.role for r in user.roles] if user else []
        await message.answer("What would you like to do next?", reply_markup=get_main_menu(roles))
        db.close()
        
    except (IndexError, ValueError):
        await message.answer("Please select a student from the keyboard.")


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
        
        tutor_user = UserService.get_user_by_telegram_id(db, message.from_user.id)
        tutor_id = tutor_user.id
        
        selected_ids = data.get('selected_ids', [])
        # If created by old flow (single student), it might be missing
        if not selected_ids and data.get('student_profile_id'):
            selected_ids = [data.get('student_profile_id')]
            
        count = 0
        for info in selected_ids: 
            # selected_ids is list of ints
            SessionService.create_session(
                db=db,
                tutor_id=tutor_id,
                student_profile_id=info,
                scheduled_at=datetime.fromisoformat(data['scheduled_at']),
                duration_minutes=duration,
                topic=data['topic']
            )
            count += 1
            
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
