from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy import func
from database.models import User, UserRole, StudentProfile, TutorProfile, Session as TSession, Report, AppSetting, ParentProfile
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AdminService:
    @staticmethod
    def get_all_students(db: Session) -> List[Dict[str, Any]]:
        results = db.query(User, StudentProfile).join(UserRole).filter(UserRole.role == "student").join(StudentProfile, User.id == StudentProfile.user_id).all()
        return [
            {
                "id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "telegram_id": user.telegram_id,
                "grade": profile.grade,
                "school": profile.school,
                "age": profile.age,
                "created_at": user.created_at
            } for user, profile in results
        ]

    @staticmethod
    def get_all_tutors(db: Session) -> List[Dict[str, Any]]:
        results = db.query(User, TutorProfile).join(UserRole).filter(UserRole.role == "tutor").join(TutorProfile, User.id == TutorProfile.user_id).all()
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
        results = db.query(User, ParentProfile).join(UserRole).filter(UserRole.role == "parent").join(ParentProfile, User.id == ParentProfile.user_id).all()
        
        parents = []
        for user, profile in results:
            # Find linked children
            children = db.query(User).join(StudentProfile, User.id == StudentProfile.user_id).filter(StudentProfile.parent_id == user.id).all()
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
            tutor_alias.full_name.label("tutor_name"),
            Report.performance_score
        ).join(student_alias, TSession.student_id == student_alias.id)\
         .join(tutor_alias, TSession.tutor_id == tutor_alias.id)\
         .outerjoin(Report, TSession.id == Report.session_id)\
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
    def get_user_sessions_detailed(db: Session, user_id: int, role: str) -> List[Dict[str, Any]]:
        student_alias = aliased(User)
        tutor_alias = aliased(User)
        
        query = db.query(
            TSession.id,
            TSession.topic,
            TSession.scheduled_at,
            TSession.duration_minutes,
            TSession.student_id,
            TSession.tutor_id,
            student_alias.full_name.label("student_name"),
            tutor_alias.full_name.label("tutor_name"),
            Report.content.label("report_content"),
            Report.performance_score.label("report_score")
        ).join(student_alias, TSession.student_id == student_alias.id)\
         .join(tutor_alias, TSession.tutor_id == tutor_alias.id)\
         .outerjoin(Report, TSession.id == Report.session_id)

        if role == "tutor":
            query = query.filter(TSession.tutor_id == user_id)
        else:
            query = query.filter(TSession.student_id == user_id)

        sessions = []
        for s in query.all():
            sessions.append({
                "id": s.id,
                "topic": s.topic,
                "scheduled_at": s.scheduled_at,
                "duration_minutes": s.duration_minutes,
                "student_name": s.student_name,
                "tutor_name": s.tutor_name,
                "other_party": s.student_name if role == "tutor" else s.tutor_name,
                "report": {
                    "content": s.report_content,
                    "score": s.report_score
                } if s.report_content else None
            })
        return sessions

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

    @staticmethod
    def get_all_reports(db: Session) -> List[Dict[str, Any]]:
        student_alias = aliased(User)
        tutor_alias = aliased(User)
        
        results = db.query(
            Report.id,
            Report.content,
            Report.performance_score,
            Report.created_at,
            TSession.topic,
            student_alias.full_name.label("student_name"),
            tutor_alias.full_name.label("tutor_name")
        ).join(TSession, Report.session_id == TSession.id)\
         .join(student_alias, TSession.student_id == student_alias.id)\
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
