from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from database.models import User, UserRole, StudentProfile, TutorProfile, Session as TSession, Report
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AdminService:
    @staticmethod
    def get_all_students(db: Session) -> List[User]:
        return db.query(User).join(UserRole).filter(UserRole.role == "student").options(
            joinedload(User.roles)
        ).all()

    @staticmethod
    def get_all_tutors(db: Session) -> List[User]:
        return db.query(User).join(UserRole).filter(UserRole.role == "tutor").options(
            joinedload(User.roles)
        ).all()

    @staticmethod
    def get_student_details(db: Session) -> List[Dict[str, Any]]:
        students = db.query(User, StudentProfile).join(UserRole).filter(UserRole.role == "student").join(StudentProfile, User.id == StudentProfile.user_id).all()
        result = []
        for user, profile in students:
            result.append({
                "id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "telegram_id": user.telegram_id,
                "grade": profile.grade,
                "school": profile.school,
                "age": profile.age,
                "created_at": user.created_at
            })
        return result

    @staticmethod
    def get_tutor_details(db: Session) -> List[Dict[str, Any]]:
        tutors = db.query(User, TutorProfile).join(UserRole).filter(UserRole.role == "tutor").join(TutorProfile, User.id == TutorProfile.user_id).all()
        result = []
        for user, profile in tutors:
            result.append({
                "id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "telegram_id": user.telegram_id,
                "subjects": profile.subjects,
                "education": profile.education,
                "experience_years": profile.experience_years,
                "verified": profile.verified,
                "created_at": user.created_at
            })
        return result

    @staticmethod
    def get_session_stats(db: Session, period: str = "daily") -> Dict[str, Any]:
        now = datetime.utcnow()
        if period == "daily":
            start_date = now - timedelta(days=1)
        elif period == "weekly":
            start_date = now - timedelta(weeks=1)
        elif period == "monthly":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=1)

        total_sessions = db.query(TSession).filter(TSession.scheduled_at >= start_date).count()
        total_duration = db.query(func.sum(TSession.duration_minutes)).filter(TSession.scheduled_at >= start_date).scalar() or 0
        total_reports = db.query(Report).filter(Report.created_at >= start_date).count()
        avg_score = db.query(func.avg(Report.performance_score)).filter(Report.created_at >= start_date).scalar() or 0

        sessions = db.query(TSession).filter(TSession.scheduled_at >= start_date).all()
        
        return {
            "period": period,
            "total_sessions": total_sessions,
            "total_duration_minutes": total_duration,
            "total_reports": total_reports,
            "average_performance_score": float(avg_score),
            "sessions": sessions
        }
