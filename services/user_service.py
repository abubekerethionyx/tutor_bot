from sqlalchemy.orm import Session, joinedload
from database.models import User, UserRole, StudentProfile, TutorProfile, ParentProfile
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
        if telegram_id is None:
            return None
        return db.query(User).options(joinedload(User.roles)).filter(User.telegram_id == telegram_id).first()

    @staticmethod
    def create_user(db: Session, telegram_id: int, full_name: str, phone: str = None) -> User:
        existing = UserService.get_user_by_telegram_id(db, telegram_id)
        if existing:
            if full_name: existing.full_name = full_name
            if phone: existing.phone = phone
            db.commit()
            return existing
            
        user = User(telegram_id=telegram_id, full_name=full_name, phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def assign_role(db: Session, user_id: int, role: str) -> UserRole:
        existing = db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role == role).first()
        if existing:
            return existing
            
        user_role = UserRole(user_id=user_id, role=role)
        db.add(user_role)
        db.commit()
        db.refresh(user_role)
        return user_role

    @staticmethod
    def create_student_profile(db: Session, full_name: str, grade: str, school: str, age: int, 
                               user_id: Optional[int] = None, parent_id: Optional[int] = None) -> StudentProfile:
        """
        Creates a student profile. 
        - user_id: Set if the student has their own Telegram account.
        - parent_id: Set if this is a managed child profile.
        """
        # If user_id is provided, try to find existing profile
        if user_id:
            existing = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
            if existing:
                existing.full_name = full_name
                existing.grade = grade
                existing.school = school
                existing.age = age
                if parent_id: existing.parent_id = parent_id
                db.commit()
                return existing

        profile = StudentProfile(
            user_id=user_id, 
            parent_id=parent_id,
            full_name=full_name,
            grade=grade, 
            school=school, 
            age=age
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def create_tutor_profile(db: Session, user_id: int, subjects: str, education: str, experience_years: int) -> TutorProfile:
        existing = db.query(TutorProfile).filter(TutorProfile.user_id == user_id).first()
        if existing:
            existing.subjects = subjects
            existing.education = education
            existing.experience_years = experience_years
            db.commit()
            return existing

        profile = TutorProfile(user_id=user_id, subjects=subjects, education=education, experience_years=experience_years)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def create_parent_profile(db: Session, user_id: int, occupation: str) -> ParentProfile:
        existing = db.query(ParentProfile).filter(ParentProfile.user_id == user_id).first()
        if existing:
            existing.occupation = occupation
            db.commit()
            return existing

        profile = ParentProfile(user_id=user_id, occupation=occupation)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_student_profile(db: Session, user_id: int) -> Optional[StudentProfile]:
        return db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()

    @staticmethod
    def get_managed_children(db: Session, parent_user_id: int) -> List[StudentProfile]:
        return db.query(StudentProfile).filter(StudentProfile.parent_id == parent_user_id).all()

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
