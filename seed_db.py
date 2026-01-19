from database.db import SessionLocal
from database.models import User, UserRole, StudentProfile, TutorProfile, Session as TSession, Report, ParentProfile
from datetime import datetime, timedelta
import random

def seed_data():
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(User).count() > 0:
        print("Database already has data. Skipping seed.")
        db.close()
        return

    print("Seeding advanced data model...")
    
    # 1. Create a Parent
    parent_user = User(telegram_id=3000, full_name="John Doe (Parent)", phone="+251911111111")
    db.add(parent_user)
    db.flush()
    db.add(UserRole(user_id=parent_user.id, role="parent"))
    db.add(ParentProfile(user_id=parent_user.id, occupation="Engineer"))
    
    # 2. Create 2 Children for this Parent (Managed Students)
    child1 = StudentProfile(
        parent_id=parent_user.id,
        full_name="Alice Doe",
        grade="Grade 8",
        school="Ethio Academy",
        age=14
    )
    child2 = StudentProfile(
        parent_id=parent_user.id,
        full_name="Bob Doe",
        grade="Grade 6",
        school="Ethio Academy",
        age=12
    )
    db.add(child1)
    db.add(child2)
    
    # 3. Create a Self-Registered Student
    student_user = User(telegram_id=1001, full_name="Charlie Brown", phone="+251922222222")
    db.add(student_user)
    db.flush()
    db.add(UserRole(user_id=student_user.id, role="student"))
    student_profile = StudentProfile(
        user_id=student_user.id,
        full_name=student_user.full_name,
        grade="Grade 10",
        school="Global School",
        age=16
    )
    db.add(student_profile)

    # 4. Create Tutors
    tutors_list = []
    for i in range(1, 4):
        tutor_user = User(telegram_id=2000 + i, full_name=f"Tutor Expert {i}", phone=f"+25193300000{i}")
        db.add(tutor_user)
        db.flush()
        db.add(UserRole(user_id=tutor_user.id, role="tutor"))
        t_profile = TutorProfile(
            user_id=tutor_user.id,
            subjects="Mathematics, Science",
            education="MSc in Education",
            experience_years=5+i,
            verified=True
        )
        db.add(t_profile)
        tutors_list.append(tutor_user)

    db.commit()

    # 5. Create Sessions and Reports
    all_profiles = [child1, child2, student_profile]
    
    for i in range(10):
        profile = random.choice(all_profiles)
        tutor = random.choice(tutors_list)
        
        session = TSession(
            tutor_id=tutor.id,
            student_profile_id=profile.id,
            scheduled_at=datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23)),
            duration_minutes=60,
            topic=random.choice(["Algebra Basics", "Science Experiment", "Language Study"])
        )
        db.add(session)
        db.flush()
        
        if random.random() > 0.3:
            report = Report(
                session_id=session.id,
                tutor_id=tutor.id,
                content="Great progress today.",
                performance_score=random.randint(7, 10),
                created_at=session.scheduled_at + timedelta(hours=1)
            )
            db.add(report)

    db.commit()
    print("Advanced Seeding complete!")
    db.close()

if __name__ == "__main__":
    seed_data()
