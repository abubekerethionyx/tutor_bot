from aiogram import Bot
from sqlalchemy.orm import Session
from database.models import Session as TSession, Attendance, Report, User, StudentProfile

async def check_and_notify_parent(bot: Bot, session_id: int, db: Session):
    """
    Checks if a session has both attendance and reports.
    If so, sends a summary to the parent.
    """
    session = db.query(TSession).filter(TSession.id == session_id).first()
    if not session:
        return

    # Check attendance
    attendance = db.query(Attendance).filter(Attendance.session_id == session_id).first()
    if not attendance:
        return
        
    # Check report
    report = db.query(Report).filter(Report.session_id == session_id).first()
    if not report:
        return
        
    # Check if student has a linked parent
    student = session.student_profile
    if not student or not student.parent_id:
        return
        
    parent_user = db.query(User).filter(User.id == student.parent_id).first()
    if not parent_user or not parent_user.telegram_id:
        return
        
    # Construct message
    status_emoji = {
        "present": "✅",
        "absent": "❌",
        "late": "⏰"
    }
    status_icon = status_emoji.get(attendance.status, "❓")
    
    tutor_name = session.tutor.full_name if session.tutor else "Tutor"
    
    summary = (
        f"📩 *Session Update for {student.full_name}*\n\n"
        f"📚 *Topic*: {session.topic}\n"
        f"👨‍🏫 *Tutor*: {tutor_name}\n"
        f"📅 *Date*: {session.scheduled_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"📊 *Attendance*: {status_icon} {attendance.status.capitalize()}\n"
        f"📝 *Report*: {report.content}\n"
        f"⭐ *Score*: {report.performance_score}/10"
    )
    
    try:
        await bot.send_message(chat_id=parent_user.telegram_id, text=summary, parse_mode="Markdown")
        # Optional: log that we sent it so we don't send multiple times? 
        # For now, simplistic approach is fine.
    except Exception as e:
        print(f"Failed to send parent notification: {e}")
