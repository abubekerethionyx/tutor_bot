from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Boolean, BigInteger
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship("UserRole", back_populates="user")
    # New relationships for the advanced model
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, foreign_keys="StudentProfile.user_id")
    managed_children = relationship("StudentProfile", back_populates="parent", foreign_keys="StudentProfile.parent_id")

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # student, tutor, parent, admin

    user = relationship("User", back_populates="roles")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # The student's own account
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True) # The parent's account
    
    # Store child's name directly to support virtual students (sharing parent's account)
    # If user_id is set, this name should match user.full_name
    full_name = Column(String, nullable=False)
    grade = Column(String)
    school = Column(String)
    age = Column(Integer)

    user = relationship("User", foreign_keys=[user_id], back_populates="student_profile")
    parent = relationship("User", foreign_keys=[parent_id], back_populates="managed_children")
    
    # Links to sessions and enrollments
    sessions = relationship("Session", back_populates="student_profile")
    enrollments = relationship("Enrollment", back_populates="student_profile")

class TutorProfile(Base):
    __tablename__ = "tutor_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    subjects = Column(String)
    education = Column(String)
    experience_years = Column(Integer)
    verified = Column(Boolean, default=False)

    user = relationship("User", foreign_keys=[user_id])


class ParentProfile(Base):
    __tablename__ = "parent_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    occupation = Column(String)
    last_report_sent_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])


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
    student_profile_id = Column(Integer, ForeignKey("student_profiles.id")) # Changed from student_id
    tutor_user_id = Column(Integer, ForeignKey("users.id")) # Changed from tutor_id
    start_date = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

    student_profile = relationship("StudentProfile", back_populates="enrollments")
    tutor = relationship("User", foreign_keys=[tutor_user_id])


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey("users.id"))
    student_profile_id = Column(Integer, ForeignKey("student_profiles.id")) # Link to profile, not user
    scheduled_at = Column(DateTime)
    duration_minutes = Column(Integer)
    topic = Column(String)

    student_profile = relationship("StudentProfile", back_populates="sessions")
    tutor = relationship("User", foreign_keys=[tutor_id])
    
    attendance = relationship("Attendance", back_populates="session")
    report = relationship("Report", back_populates="session", uselist=False)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    # In attendance, we track which profile was present
    student_profile_id = Column(Integer, ForeignKey("student_profiles.id"))
    status = Column(String)  # present / absent / late

    session = relationship("Session", back_populates="attendance")
    student_profile = relationship("StudentProfile")


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
