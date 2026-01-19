from database.db import SessionLocal
from database.models import User, UserRole, StudentProfile, TutorProfile, Session as TSession, Report
from datetime import datetime, timedelta
import random

def seed_data():
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(User).count() > 0:
        print("Database already has data. Skipping seed.")
        db.close()
        return

    print("Seeding dummy data...")
    
    # Create Students
    for i in range(1, 6):
        user = User(telegram_id=1000 + i, full_name=f"Student {i}", phone=f"+25191100000{i}")
        db.add(user)
        db.flush()
        
        role = UserRole(user_id=user.id, role="student")
        db.add(role)
        
        profile = StudentProfile(
            user_id=user.id, 
            grade=f"Grade {random.randint(6, 12)}", 
            school="Ethio Academy", 
            age=12 + i
        )
        db.add(profile)

    # Create Tutors
    for i in range(1, 4):
        user = User(telegram_id=2000 + i, full_name=f"Tutor {i}", phone=f"+25192200000{i}")
        db.add(user)
        db.flush()
        
        role = UserRole(user_id=user.id, role="tutor")
        db.add(role)
        
        profile = TutorProfile(
            user_id=user.id, 
            subjects="Math, Physics, English", 
            education="BSc in Engineering", 
            experience_years=i + 2,
            verified=True
        )
        db.add(profile)

    db.commit()

    # Create Sessions and Reports
    students = db.query(User).join(UserRole).filter(UserRole.role == "student").all()
    tutors = db.query(User).join(UserRole).filter(UserRole.role == "tutor").all()

    for i in range(10):
        student = random.choice(students)
        tutor = random.choice(tutors)
        
        session = TSession(
            tutor_id=tutor.id,
            student_id=student.id,
            scheduled_at=datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23)),
            duration_minutes=random.choice([60, 90, 120]),
            topic=random.choice(["Algebra Basics", "Quantum Physics", "Shakespeare Intro", "Calculus I"])
        )
        db.add(session)
        db.flush()
        
        if random.random() > 0.3: # 70% chance of having a report
            report = Report(
                session_id=session.id,
                tutor_id=tutor.id,
                content="The student is progressing well but needs more practice on problem solving.",
                performance_score=random.randint(6, 10),
                created_at=session.scheduled_at + timedelta(hours=2)
            )
            db.add(report)

    db.commit()
    print("Seeding complete!")
    db.close()

if __name__ == "__main__":
    seed_data()
