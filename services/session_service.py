from sqlalchemy.orm import Session
from database.models import Session as TSession, Enrollment, Attendance, Report
from datetime import datetime
from typing import List, Optional

class SessionService:
    @staticmethod
    def enroll_student(db: Session, student_id: int, tutor_id: int) -> Enrollment:
        enrollment = Enrollment(student_id=student_id, tutor_id=tutor_id)
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    @staticmethod
    def get_enrollments_for_student(db: Session, student_id: int) -> List[Enrollment]:
        return db.query(Enrollment).filter(Enrollment.student_id == student_id, Enrollment.active == True).all()

    @staticmethod
    def get_enrollments_for_tutor(db: Session, tutor_id: int) -> List[Enrollment]:
        return db.query(Enrollment).filter(Enrollment.tutor_id == tutor_id, Enrollment.active == True).all()

    @staticmethod
    def create_session(db: Session, tutor_id: int, student_id: int, scheduled_at: datetime, duration_minutes: int, topic: str) -> TSession:
        session = TSession(
            tutor_id=tutor_id,
            student_id=student_id,
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
        if role == "tutor":
            return db.query(TSession).filter(TSession.tutor_id == user_id).all()
        else:
            return db.query(TSession).filter(TSession.student_id == user_id).all()

    @staticmethod
    def mark_attendance(db: Session, session_id: int, user_id: int, status: str) -> Attendance:
        attendance = Attendance(session_id=session_id, user_id=user_id, status=status)
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
