from sqlalchemy.orm import Session
from database.models import Session as TSession, Enrollment, Attendance, Report, StudentProfile, User
from datetime import datetime
from typing import List, Optional

class SessionService:
    @staticmethod
    def enroll_student(db: Session, student_profile_id: int, tutor_user_id: int) -> Enrollment:
        enrollment = Enrollment(student_profile_id=student_profile_id, tutor_user_id=tutor_user_id)
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def get_enrollments_for_student_profile(db: Session, student_profile_id: int) -> List[Enrollment]:
        return db.query(Enrollment).filter(Enrollment.student_profile_id == student_profile_id, Enrollment.active == True).all()

    @staticmethod
    def get_enrollments_for_tutor(db: Session, tutor_user_id: int) -> List[Enrollment]:
        return db.query(Enrollment).filter(Enrollment.tutor_user_id == tutor_user_id, Enrollment.active == True).all()

    @staticmethod
    def create_session(db: Session, tutor_id: int, student_profile_id: int, scheduled_at: datetime, duration_minutes: int, topic: str) -> TSession:
        session = TSession(
            tutor_id=tutor_id,
            student_profile_id=student_profile_id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            topic=topic
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_user_sessions(db: Session, user_id: int, role: str) -> List[TSession]:
        """
        Fetches sessions for a user based on their role.
        For students, it finds profiles linked to their user_id.
        """
        if role == "tutor":
            return db.query(TSession).filter(TSession.tutor_id == user_id).order_by(TSession.scheduled_at.desc()).all()
        else:
            # Student: find their profile first
            profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
            if not profile:
                return []
            return db.query(TSession).filter(TSession.student_profile_id == profile.id).order_by(TSession.scheduled_at.desc()).all()

    @staticmethod
    def get_profile_sessions(db: Session, profile_id: int) -> List[TSession]:
        return db.query(TSession).filter(TSession.student_profile_id == profile_id).order_by(TSession.scheduled_at.desc()).all()

    @staticmethod
    def mark_attendance(db: Session, session_id: int, student_profile_id: int, status: str) -> Attendance:
        attendance = Attendance(session_id=session_id, student_profile_id=student_profile_id, status=status)
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

    @staticmethod
    def create_report(db: Session, session_id: int, tutor_id: int, content: str, performance_score: int) -> Report:
        report = Report(
            session_id=session_id,
            tutor_id=tutor_id,
            content=content,
            performance_score=performance_score
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
