from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship("UserRole", back_populates="user")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # student, tutor, parent, admin

    user = relationship("User", back_populates="roles")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    grade = Column(String)
    school = Column(String)
    age = Column(Integer)

    parent_id = Column(Integer, ForeignKey("users.id"))

    parent = relationship("User", foreign_keys=[parent_id])


class TutorProfile(Base):
    __tablename__ = "tutor_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    subjects = Column(String)
    education = Column(String)
    experience_years = Column(Integer)
    verified = Column(Boolean, default=False)


class ParentProfile(Base):
    __tablename__ = "parent_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    occupation = Column(String)
    last_report_sent_at = Column(DateTime, nullable=True)


class ParentReportLog(Base):
    __tablename__ = "parent_report_logs"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("users.id"))
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # success, failed
    error_message = Column(Text, nullable=True)


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    tutor_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey("users.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    scheduled_at = Column(DateTime)
    duration_minutes = Column(Integer)
    topic = Column(String)

    attendance = relationship("Attendance", back_populates="session")
    report = relationship("Report", back_populates="session", uselist=False)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)  # present / absent / late

    session = relationship("Session", back_populates="attendance")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    tutor_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    performance_score = Column(Integer)  # 1–10
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="report")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    entity = Column(String)
    entity_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)


class AppSetting(Base):
    __tablename__ = "app_settings"
    
    key = Column(String, primary_key=True)
    value = Column(String)
    description = Column(String)
