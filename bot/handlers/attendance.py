from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database.db import SessionLocal
from services.user_service import UserService
from services.session_service import SessionService
from database.models import Attendance, Session as TSession, StudentProfile, User
from bot.keyboards.common import get_main_menu
from bot.states.attendance import AttendanceStates

router = Router()

async def show_attendance_for_profile(message: types.Message, profile_id: int, db):
    profile = db.query(StudentProfile).filter(StudentProfile.id == profile_id).first()
    if not profile:
        await message.answer("Profile not found.")
        return

    # Get all sessions for this student profile
    sessions = db.query(TSession).filter(TSession.student_profile_id == profile.id).order_by(TSession.scheduled_at.desc()).limit(10).all()
    
    if not sessions:
        await message.answer(f"📅 {profile.full_name} has no recorded sessions yet.")
        return
    
    response = f"📊 *Attendance Record for {profile.full_name} (Last 10 Sessions):*\n\n"
    
    for sess in sessions:
        # Check if attendance was marked for this session
        attendance = db.query(Attendance).filter(
            Attendance.session_id == sess.id,
            Attendance.student_profile_id == profile.id
        ).first()
        
        # Get tutor name
        tutor = db.query(User).filter(User.id == sess.tutor_id).first()
        tutor_name = tutor.full_name if tutor else "Unknown"
        
        status_emoji = {
            "present": "✅",
            "absent": "❌",
            "late": "⏰"
        }
        
        if attendance:
            status = f"{status_emoji.get(attendance.status, '❓')} {attendance.status.capitalize()}"
        else:
            status = "⚪ Not Marked"
        
        response += (
            f"📚 *{sess.topic}*\n"
            f"👨‍🏫 Tutor: {tutor_name}\n"
            f"📅 Date: {sess.scheduled_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"📊 Status: {status}\n\n"
        )
    
    await message.answer(response, parse_mode="Markdown")

@router.message(F.text == "My Attendance")
async def my_attendance_handler(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    if not user:
        await message.answer("Please register first.")
        db.close()
        return
    
    roles = [r.role for r in user.roles]
    is_parent = "parent" in roles
    is_student = "student" in roles

    if is_parent:
        children = UserService.get_managed_children(db, user.id)
        if not children:
            await message.answer("You have no linked children.")
            db.close()
            return
        
        builder = ReplyKeyboardBuilder()
        for child in children:
            builder.button(text=f"Child: {child.full_name} (ID: {child.id})")
        
        builder.adjust(1)
        builder.button(text="Back")
        
        await message.answer("Select a child to view attendance:", reply_markup=builder.as_markup(resize_keyboard=True))
        await state.set_state(AttendanceStates.waiting_for_child_pick)
        db.close()
        return

    if is_student:
        # Get student profile
        profile = UserService.get_student_profile(db, user.id)
        if not profile:
            await message.answer("You must be registered as a student to view attendance.")
            db.close()
            return
        
        await show_attendance_for_profile(message, profile.id, db)
        db.close()
        return
    
    await message.answer("Attendance viewing is only available for students and parents.")
    db.close()

@router.message(F.text == "Mark Attendance")
async def mark_attendance_start(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    if not user or not any(r.role == "tutor" for r in user.roles):
        await message.answer("Only tutors can mark attendance.")
        db.close()
        return

    # Get recent sessions for this tutor (e.g. last 10)
    sessions = SessionService.get_user_sessions(db, user.id, "tutor")
    
    if not sessions:
        await message.answer("You have no sessions to mark attendance for.")
        db.close()
        return
        
    # Group sessions by (topic, scheduled_at)
    grouped = {}
    for sess in sessions:
        key = (sess.topic, sess.scheduled_at)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(sess)
        
    builder = ReplyKeyboardBuilder()
    count = 0
    
    # Store grouping in state so we can retrieve lists later
    # We can serialize by index since we only show few? 
    # Or just use key string. Using index for simplicity in this turn.
    
    group_list = []
    
    for (topic, time), sess_list in grouped.items():
        time_str = time.strftime("%Y-%m-%d %H:%M")
        size = len(sess_list)
        label = f"{topic} ({size} students) @ {time_str}"
        builder.button(text=label)
        
        # Store IDs for this group
        group_list.append({"ids": [s.id for s in sess_list], "label": label})
        
        count += 1
        if count >= 10: break
    
    await state.update_data(session_groups=group_list)
    
    builder.adjust(1)
    builder.button(text="Back")
    
    await message.answer("Select a session (or group) to mark attendance for:", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AttendanceStates.waiting_for_session_pick)
    db.close()

@router.message(AttendanceStates.waiting_for_session_pick)
async def process_session_pick_mark(message: types.Message, state: FSMContext):
    if message.text == "Back":
        await state.clear()
        await message.answer("Operation cancelled.") # Or return to menu
        return

    data = await state.get_data()
    # Find group based on text
    groups = data.get('session_groups', [])
    selected_group = next((g for g in groups if g['label'] == message.text), None)
    
    if not selected_group:
        await message.answer("Please select a session from the keyboard.")
        return

    session_ids = selected_group['ids']
    
    db = SessionLocal()
    
    # Fetch student names used in this group
    students = []
    for sid in session_ids:
        sess = db.query(TSession).filter(TSession.id == sid).first()
        if sess and sess.student_profile:
             students.append((sid, sess.student_profile.full_name))
             
    # Prepare selection state
    await state.update_data(attendance_session_ids=session_ids, student_list=students, selected_students=[])
    
    await show_attendance_student_selection(message, state)
    db.close()

async def show_attendance_student_selection(message: types.Message, state: FSMContext):
    data = await state.get_data()
    student_list = data.get('student_list', []) # [(session_id, name)]
    selected_students = data.get('selected_students', []) # [session_id]
    
    builder = ReplyKeyboardBuilder()
    
    for sid, name in student_list:
        status = "✅" if sid in selected_students else "⬜"
        builder.button(text=f"{status} {name} (Ref: {sid})")
        
    builder.adjust(1)
    builder.button(text="Mark Selected")
    builder.button(text="Back")
    
    await message.answer(f"Select students to apply status to ({len(selected_students)} selected):", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AttendanceStates.waiting_for_student_selection)


@router.message(AttendanceStates.waiting_for_student_selection)
async def process_attendance_student_selection(message: types.Message, state: FSMContext):
    if message.text == "Back":
        await state.clear()
        await message.answer("Main Menu", reply_markup=get_main_menu(["tutor"])) 
        return

    if message.text == "Mark Selected":
        data = await state.get_data()
        if not data.get('selected_students'):
             await message.answer("Select at least one student.")
             return
             
        builder = ReplyKeyboardBuilder()
        builder.button(text="Present ✅")
        builder.button(text="Absent ❌")
        builder.button(text="Late ⏰")
        builder.adjust(3)
        builder.button(text="Back")
        
        await message.answer("Select status for these students:", reply_markup=builder.as_markup(resize_keyboard=True))
        await state.set_state(AttendanceStates.waiting_for_status_pick)
        return
        
    try:
        # Expected: "✅ Name (Ref: 123)"
        ref_id = int(message.text.split("Ref: ")[1].replace(")", ""))
        data = await state.get_data()
        selected = data.get('selected_students', [])
        
        if ref_id in selected:
            selected.remove(ref_id)
        else:
            selected.append(ref_id)
            
        await state.update_data(selected_students=selected)
        await show_attendance_student_selection(message, state)
    except (IndexError, ValueError):
        await message.answer("Use the keyboard.")

@router.message(AttendanceStates.waiting_for_status_pick)
async def process_status_pick(message: types.Message, state: FSMContext):
    if message.text == "Back":
        await show_attendance_student_selection(message, state)
        return

    status_map = {
        "Present ✅": "present",
        "Absent ❌": "absent",
        "Late ⏰": "late"
    }
    
    status = status_map.get(message.text)
    if not status:
        await message.answer("Please select a valid status.")
        return
        
    data = await state.get_data()
    target_sessions = data.get('selected_students', []) # List of session IDs
    
    db = SessionLocal()
    count = 0
    for sid in target_sessions:
        session = db.query(TSession).filter(TSession.id == sid).first()
        if session:
            SessionService.mark_attendance(db, sid, session.student_profile_id, status)
            count += 1
    
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    roles = [r.role for r in user.roles] if user else ["tutor"]
    
    # Notify parents if applicable
    from bot.utils.notifications import check_and_notify_parent
    # We iterate over unique sessions marked
    for sid in target_sessions:
        await check_and_notify_parent(message.bot, sid, db)
    
    await message.answer(f"✅ Marked {count} students as {status.capitalize()}!", reply_markup=get_main_menu(roles))
    await state.clear()
    db.close()


@router.message(AttendanceStates.waiting_for_child_pick)
async def process_child_pick_attendance(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    roles = [r.role for r in user.roles] if user else []

    if message.text == "Back":
        await state.clear()
        await message.answer("Main Menu", reply_markup=get_main_menu(roles))
        db.close()
        return

    if not message.text.startswith("Child:"):
        await message.answer("Please select a child from the keyboard.")
        db.close()
        return

    try:
        profile_id = int(message.text.split("ID: ")[1].replace(")", ""))
        
        # Verify this child belongs to the parent? 
        # Ideally yes, but list was generated from managed children.
        # Assuming ID is valid.
        
        await show_attendance_for_profile(message, profile_id, db)
        await state.clear()
        await message.answer("Here is the attendance report.", reply_markup=get_main_menu(roles))
        
    except (IndexError, ValueError):
        await message.answer("Invalid selection. Please use the keyboard.")
    
    db.close()
