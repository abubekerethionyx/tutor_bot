from aiogram import Router, types, F
from database.db import SessionLocal
from services.user_service import UserService
from database.models import Attendance, Session as TSession, StudentProfile
from bot.keyboards.common import get_main_menu

router = Router()

@router.message(F.text == "My Attendance")
async def my_attendance_handler(message: types.Message):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    if not user:
        await message.answer("Please register first.")
        db.close()
        return
    
    # Get student profile
    profile = UserService.get_student_profile(db, user.id)
    if not profile:
        await message.answer("You must be registered as a student to view attendance.")
        db.close()
        return
    
    # Get all sessions for this student profile
    sessions = db.query(TSession).filter(TSession.student_profile_id == profile.id).order_by(TSession.scheduled_at.desc()).limit(10).all()
    
    if not sessions:
        await message.answer("📅 You have no recorded sessions yet.")
        db.close()
        return
    
    response = "📊 *Your Attendance Record (Last 10 Sessions):*\n\n"
    
    for sess in sessions:
        # Check if attendance was marked for this session
        attendance = db.query(Attendance).filter(
            Attendance.session_id == sess.id,
            Attendance.student_profile_id == profile.id
        ).first()
        
        # Get tutor name
        from database.models import User
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
    db.close()
