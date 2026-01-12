from sqlalchemy.orm import Session
from database.models import User, UserRole, StudentProfile, TutorProfile, ParentProfile
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
        from sqlalchemy.orm import joinedload
        return db.query(User).options(joinedload(User.roles)).filter(User.telegram_id == telegram_id).first()

    @staticmethod
    def create_user(db: Session, telegram_id: int, full_name: str, phone: str = None) -> User:
        user = User(telegram_id=telegram_id, full_name=full_name, phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def assign_role(db: Session, user_id: int, role: str) -> UserRole:
        user_role = UserRole(user_id=user_id, role=role)
        db.add(user_role)
        db.commit()
        db.refresh(user_role)
        return user_role

    @staticmethod
    def create_student_profile(db: Session, user_id: int, grade: str, school: str, age: int, parent_id: Optional[int] = None) -> StudentProfile:
        profile = StudentProfile(user_id=user_id, grade=grade, school=school, age=age, parent_id=parent_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def create_tutor_profile(db: Session, user_id: int, subjects: str, education: str, experience_years: int) -> TutorProfile:
        profile = TutorProfile(user_id=user_id, subjects=subjects, education=education, experience_years=experience_years)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_student_profile(db: Session, user_id: int) -> Optional[StudentProfile]:
        return db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()

    @staticmethod
    def get_tutor_profile(db: Session, user_id: int) -> Optional[TutorProfile]:
        return db.query(TutorProfile).filter(TutorProfile.user_id == user_id).first()

    @staticmethod
    def get_parent_profile(db: Session, user_id: int) -> Optional[ParentProfile]:
        return db.query(ParentProfile).filter(ParentProfile.user_id == user_id).first()

    @staticmethod
    def search_tutors(db: Session, subject: Optional[str] = None) -> List[User]:
        query = db.query(User).join(UserRole).filter(UserRole.role == "tutor")
        if subject:
            query = query.join(TutorProfile).filter(TutorProfile.subjects.contains(subject))
        return query.all()
