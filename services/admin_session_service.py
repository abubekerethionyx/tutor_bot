from sqlalchemy.orm import Session
from database.models import User, StudentProfile, Session as TSession, Attendance, Report
from typing import List, Dict, Any, Optional

class AdminSessionService:
    """Service for admin to view detailed session information"""
    
    @staticmethod
    def get_user_sessions_detailed(db: Session, user_id: int, role: str) -> List[Dict[str, Any]]:
        """
        Get detailed sessions for a user (student or tutor) with attendance and reports
        """
        sessions = []
        
        if role == "tutor":
            # Get all sessions where this user is the tutor
            tutor_sessions = db.query(TSession).filter(TSession.tutor_id == user_id).order_by(TSession.scheduled_at.desc()).all()
            
            for sess in tutor_sessions:
                student_profile = db.query(StudentProfile).filter(StudentProfile.id == sess.student_profile_id).first()
                attendance = db.query(Attendance).filter(
                    Attendance.session_id == sess.id,
                    Attendance.student_profile_id == sess.student_profile_id
                ).first()
                report = db.query(Report).filter(Report.session_id == sess.id).first()
                
                sessions.append({
                    "id": sess.id,
                    "topic": sess.topic,
                    "scheduled_at": sess.scheduled_at,
                    "duration_minutes": sess.duration_minutes,
                    "student_name": student_profile.full_name if student_profile else "Unknown",
                    "student_id": student_profile.id if student_profile else None,
                    "attendance": {
                        "status": attendance.status if attendance else None,
                        "marked": attendance is not None
                    },
                    "report": {
                        "exists": report is not None,
                        "score": report.performance_score if report else None,
                        "content": report.content if report else None
                    }
                })
        
        elif role == "student":
            # Get student profile first
            student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
            
            if student_profile:
                # Get all sessions for this student profile
                student_sessions = db.query(TSession).filter(
                    TSession.student_profile_id == student_profile.id
                ).order_by(TSession.scheduled_at.desc()).all()
                
                for sess in student_sessions:
                    tutor = db.query(User).filter(User.id == sess.tutor_id).first()
                    attendance = db.query(Attendance).filter(
                        Attendance.session_id == sess.id,
                        Attendance.student_profile_id == student_profile.id
                    ).first()
                    report = db.query(Report).filter(Report.session_id == sess.id).first()
                    
                    sessions.append({
                        "id": sess.id,
                        "topic": sess.topic,
                        "scheduled_at": sess.scheduled_at,
                        "duration_minutes": sess.duration_minutes,
                        "tutor_name": tutor.full_name if tutor else "Unknown",
                        "tutor_id": tutor.id if tutor else None,
                        "attendance": {
                            "status": attendance.status if attendance else None,
                            "marked": attendance is not None
                        },
                        "report": {
                            "exists": report is not None,
                            "score": report.performance_score if report else None,
                            "content": report.content if report else None
                        }
                    })
        
        return sessions
    
    @staticmethod
    def get_profile_sessions_detailed(db: Session, profile_id: int) -> List[Dict[str, Any]]:
        """
        Get detailed sessions for a specific student profile (for managed children)
        """
        sessions = []
        student_profile = db.query(StudentProfile).filter(StudentProfile.id == profile_id).first()
        
        if not student_profile:
            return []
        
        student_sessions = db.query(TSession).filter(
            TSession.student_profile_id == profile_id
        ).order_by(TSession.scheduled_at.desc()).all()
        
        for sess in student_sessions:
            tutor = db.query(User).filter(User.id == sess.tutor_id).first()
            attendance = db.query(Attendance).filter(
                Attendance.session_id == sess.id,
                Attendance.student_profile_id == profile_id
            ).first()
            report = db.query(Report).filter(Report.session_id == sess.id).first()
            
            sessions.append({
                "id": sess.id,
                "topic": sess.topic,
                "scheduled_at": sess.scheduled_at,
                "duration_minutes": sess.duration_minutes,
                "student_name": student_profile.full_name,
                "tutor_name": tutor.full_name if tutor else "Unknown",
                "tutor_id": tutor.id if tutor else None,
                "attendance": {
                    "status": attendance.status if attendance else None,
                    "marked": attendance is not None
                },
                "report": {
                    "exists": report is not None,
                    "score": report.performance_score if report else None,
                    "content": report.content if report else None
                }
            })
        
        return sessions
