from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy import func
from database.models import User, UserRole, StudentProfile, TutorProfile, Session as TSession, Report, AppSetting, ParentProfile
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AdminService:
    @staticmethod
    def get_all_students(db: Session) -> List[Dict[str, Any]]:
        # This now returns all student profiles, whether they have their own account or not
        results = db.query(StudentProfile).all()
        
        students = []
        for profile in results:
            # Try to get phone from their own account or parent's account
            phone = None
            email = None # if we had email
            telegram_id = None
            
            if profile.user:
                phone = profile.user.phone
                telegram_id = profile.user.telegram_id
            elif profile.parent:
                phone = profile.parent.phone
                telegram_id = profile.parent.telegram_id # Mark as shared in UI?

            students.append({
                "id": profile.id,
                "full_name": profile.full_name,
                "phone": phone,
                "telegram_id": telegram_id,
                "grade": profile.grade,
                "school": profile.school,
                "age": profile.age,
                "managed": profile.parent_id is not None
            })
        return students

    @staticmethod
    def get_all_tutors(db: Session) -> List[Dict[str, Any]]:
        results = db.query(User, TutorProfile).join(TutorProfile, User.id == TutorProfile.user_id).all()
        return [
            {
                "id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "telegram_id": user.telegram_id,
                "subjects": profile.subjects,
                "education": profile.education,
                "experience_years": profile.experience_years,
                "verified": profile.verified,
                "created_at": user.created_at
            } for user, profile in results
        ]

    @staticmethod
    def get_all_parents(db: Session) -> List[Dict[str, Any]]:
        results = db.query(User, ParentProfile).join(ParentProfile, User.id == ParentProfile.user_id).all()
        
        parents = []
        for user, profile in results:
            # Find linked children profiles
            children = db.query(StudentProfile).filter(StudentProfile.parent_id == user.id).all()
            children_names = [c.full_name for c in children]
            
            parents.append({
                "id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "telegram_id": user.telegram_id,
                "occupation": profile.occupation,
                "last_report_sent": profile.last_report_sent_at,
                "children": children_names,
                "created_at": user.created_at
            })
        return parents

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

        tutor_alias = aliased(User)
        
        sessions_query = db.query(
            TSession.id,
            TSession.topic,
            TSession.scheduled_at,
            TSession.duration_minutes,
            TSession.tutor_id,
            TSession.student_profile_id,
            StudentProfile.full_name.label("student_name"),
            tutor_alias.full_name.label("tutor_name"),
            Report.performance_score
        ).join(StudentProfile, TSession.student_profile_id == StudentProfile.id)\
         .join(tutor_alias, TSession.tutor_id == tutor_alias.id)\
         .outerjoin(Report, TSession.id == Report.session_id)\
         .filter(TSession.scheduled_at >= start_date)
        
        sessions = [
            {
                "id": s.id,
                "topic": s.topic,
                "scheduled_at": s.scheduled_at,
                "duration_minutes": s.duration_minutes,
                "student_id": s.student_profile_id,
                "tutor_id": s.tutor_id,
                "student_name": s.student_name,
                "tutor_name": s.tutor_name,
                "report_score": s.performance_score
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

    @staticmethod
    def get_all_reports(db: Session) -> List[Dict[str, Any]]:
        tutor_alias = aliased(User)
        
        results = db.query(
            Report.id,
            Report.content,
            Report.performance_score,
            Report.created_at,
            TSession.topic,
            StudentProfile.full_name.label("student_name"),
            tutor_alias.full_name.label("tutor_name")
        ).join(TSession, Report.session_id == TSession.id)\
         .join(StudentProfile, TSession.student_profile_id == StudentProfile.id)\
         .join(tutor_alias, TSession.tutor_id == tutor_alias.id)\
         .order_by(Report.created_at.desc()).all()
         
        return [
            {
                "id": r.id,
                "content": r.content,
                "performance_score": r.performance_score,
                "created_at": r.created_at,
                "topic": r.topic,
                "student_name": r.student_name,
                "tutor_name": r.tutor_name
            } for r in results
        ]

    # Settings methods remain the same
    @staticmethod
    def get_settings(db: Session) -> Dict[str, str]:
        settings = db.query(AppSetting).all()
        return {s.key: s.value for s in settings}

    @staticmethod
    def update_setting(db: Session, key: str, value: str) -> bool:
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        if not setting:
            setting = AppSetting(key=key, value=value)
            db.add(setting)
        else:
            setting.value = value
        db.commit()
        return True
