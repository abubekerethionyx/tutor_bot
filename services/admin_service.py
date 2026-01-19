from sqlalchemy.orm import Session, joinedload, aliased
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

        student_alias = aliased(User)
        tutor_alias = aliased(User)
        
        sessions_query = db.query(
            TSession.id,
            TSession.topic,
            TSession.scheduled_at,
            TSession.duration_minutes,
            TSession.student_id,
            TSession.tutor_id,
            student_alias.full_name.label("student_name"),
            tutor_alias.full_name.label("tutor_name")
        ).join(student_alias, TSession.student_id == student_alias.id)\
         .join(tutor_alias, TSession.tutor_id == tutor_alias.id)\
         .filter(TSession.scheduled_at >= start_date)
        
        sessions = [
            {
                "id": s.id,
                "topic": s.topic,
                "scheduled_at": s.scheduled_at,
                "duration_minutes": s.duration_minutes,
                "student_id": s.student_id,
                "tutor_id": s.tutor_id,
                "student_name": s.student_name,
                "tutor_name": s.tutor_name
            } for s in sessions_query.all()
        ]
        
        return {
            "period": period,
            "total_sessions": total_sessions,
            "total_duration_minutes": total_duration,
            "total_reports": total_reports,
            "average_performance_score": float(avg_score),
            "sessions": sessions
        }

    @staticmethod
    def verify_tutor(db: Session, tutor_id: int, status: bool) -> bool:
        profile = db.query(TutorProfile).filter(TutorProfile.user_id == tutor_id).first()
        if profile:
            profile.verified = status
            db.commit()
            return True
        return False
