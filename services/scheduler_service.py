import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database.db import SessionLocal
from database.models import User, StudentProfile, Session as TSession, Report, AppSetting, ParentReportLog, ParentProfile
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def send_daily_reports(bot: Bot):
    db = SessionLocal()
    try:
        # Get all parents
        parents = db.query(User).join(User.roles).filter(User.roles.any(role="parent")).all()
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        for parent in parents:
            # Find children
            children = db.query(User).join(StudentProfile, User.id == StudentProfile.user_id).filter(StudentProfile.parent_id == parent.id).all()
            
            if not children:
                continue
                
            report_msg = "☀️ *Daily Session Report Summary:*\n\n"
            found_activity = False
            
            for child in children:
                # Find sessions from yesterday with reports
                sessions = db.query(TSession).filter(
                    TSession.student_id == child.id,
                    TSession.scheduled_at >= yesterday
                ).join(Report).all()
                
                if sessions:
                    found_activity = True
                    report_msg += f"👶 *{child.full_name}:*\n"
                    for sess in sessions:
                        report_msg += f"🔹 {sess.topic}\n"
                        report_msg += f"⭐ Score: {sess.report.performance_score}/10\n"
                        report_msg += f"📝 {sess.report.content}\n\n"
            
            if found_activity:
                try:
                    await bot.send_message(parent.telegram_id, report_msg, parse_mode="Markdown")
                    logger.info(f"Sent daily report to parent {parent.id}")
                    
                    # Log success
                    log = ParentReportLog(parent_id=parent.id, status="success")
                    db.add(log)
                    
                    # Update profile
                    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent.id).first()
                    if profile:
                        profile.last_report_sent_at = datetime.utcnow()
                    
                    db.commit()
                except Exception as e:
                    logger.error(f"Failed to send report to parent {parent.id}: {e}")
                    log = ParentReportLog(parent_id=parent.id, status="failed", error_message=str(e))
                    db.add(log)
                    db.commit()
    finally:
        db.close()

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    db = SessionLocal()
    
    # Get configuration time from DB, default to 08:00
    time_setting = db.query(AppSetting).filter(AppSetting.key == "daily_report_time").first()
    report_time = time_setting.value if time_setting else "08:00"
    db.close()
    
    hour, minute = map(int, report_time.split(":"))
    
    scheduler.add_job(send_daily_reports, 'cron', hour=hour, minute=minute, args=[bot], id="daily_reports")
    scheduler.start()
    logger.info(f"Scheduler started. Daily reports scheduled for {report_time}")
    return scheduler

async def update_scheduler_time(scheduler: AsyncIOScheduler, bot: Bot, new_time: str):
    # format: HH:MM
    try:
        hour, minute = map(int, new_time.split(":"))
        scheduler.remove_job("daily_reports")
        scheduler.add_job(send_daily_reports, 'cron', hour=hour, minute=minute, args=[bot], id="daily_reports")
        logger.info(f"Daily reports rescheduled for {new_time}")
        return True
    except Exception as e:
        logger.error(f"Failed to update scheduler time: {e}")
        return False
