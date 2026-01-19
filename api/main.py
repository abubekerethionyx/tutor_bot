from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
import os

from database.db import engine, Base, SessionLocal
from database import models
from api import schemas
from services.user_service import UserService
from services.session_service import SessionService
from services.admin_service import AdminService
from api import admin_routes
from api.auth import verify_admin
from config import settings
from typing import List, Optional

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tutormula API")

# Include modular admin routes
app.include_router(admin_routes.router)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Welcome to Tutormula API"}

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    return FileResponse("api/admin.html")

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page():
    return FileResponse("api/login.html")

@app.post("/admin/login")
async def admin_login(data: dict):
    if data.get("secret") == settings.ADMIN_SECRET:
        return {"token": settings.ADMIN_SECRET, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid secret")

@app.get("/health")
async def health():
    return {"status": "healthy"}

# --- Tutor Routes ---

@app.get("/tutors/search", response_model=List[schemas.TutorSearchResponse])
def search_tutors(subject: Optional[str] = Query(None), db: Session = Depends(get_db)):
    tutors = UserService.search_tutors(db, subject)
    # We need to include the profile in the response if it exists
    results = []
    for tutor in tutors:
        tutor_data = schemas.TutorSearchResponse.model_validate(tutor)
        profile = UserService.get_tutor_profile(db, tutor.id)
        if profile:
            tutor_data.tutor_profile = schemas.TutorProfileResponse.model_validate(profile)
        results.append(tutor_data)
    return results

# --- Enrollment Routes ---

@app.post("/enrollments/", response_model=schemas.EnrollmentResponse)
def enroll_student(enrollment: schemas.EnrollmentCreate, db: Session = Depends(get_db)):
    return SessionService.enroll_student(db, enrollment.student_id, enrollment.tutor_id)

@app.get("/enrollments/student/{student_id}", response_model=List[schemas.EnrollmentResponse])
def get_student_enrollments(student_id: int, db: Session = Depends(get_db)):
    return SessionService.get_enrollments_for_student(db, student_id)

# --- Session Routes ---

@app.post("/sessions/", response_model=schemas.SessionResponse)
def create_session(session: schemas.SessionCreate, db: Session = Depends(get_db)):
    return SessionService.create_session(
        db, 
        session.tutor_id, 
        session.student_profile_id, 
        session.scheduled_at, 
        session.duration_minutes, 
        session.topic
    )

@app.get("/sessions/user/{user_id}", response_model=List[schemas.SessionResponse])
def get_user_sessions(user_id: int, role: str = Query("student"), db: Session = Depends(get_db)):
    results = SessionService.get_user_sessions(db, user_id, role)
    # Convert to schema compatible format
    sessions = []
    for s in results:
        tutor = db.query(models.User).filter(models.User.id == s.tutor_id).first()
        sessions.append(schemas.SessionResponse(
            id=s.id,
            tutor_id=s.tutor_id,
            student_profile_id=s.student_profile_id,
            tutor_name=tutor.full_name if tutor else "Unknown",
            student_name=s.student_profile.full_name if s.student_profile else "Unknown",
            scheduled_at=s.scheduled_at,
            duration_minutes=s.duration_minutes,
            topic=s.topic
        ))
    return sessions

# --- Admin Routes ---

@app.get("/admin/students", response_model=List[schemas.AdminStudentDetail])
def get_admin_students(db: Session = Depends(get_db), admin: str = Depends(verify_admin)):
    return AdminService.get_all_students(db)

@app.get("/admin/tutors", response_model=List[schemas.AdminTutorDetail])
def get_admin_tutors(db: Session = Depends(get_db), admin: str = Depends(verify_admin)):
    return AdminService.get_all_tutors(db)

@app.get("/admin/parents", response_model=List[schemas.AdminParentDetail])
def get_admin_parents(db: Session = Depends(get_db), admin: str = Depends(verify_admin)):
    return AdminService.get_all_parents(db)

@app.get("/admin/reports/sessions", response_model=schemas.SessionReportSummary)
def get_admin_session_report(
    period: str = Query("daily", enum=["daily", "weekly", "monthly"]),
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    return AdminService.get_session_stats(db, period)

@app.post("/admin/tutors/{tutor_id}/verify")
def verify_tutor(
    tutor_id: int,
    status: bool = Query(True),
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    success = AdminService.verify_tutor(db, tutor_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Tutor not found")
    return {"message": "Tutor status updated"}

@app.get("/admin/users/{user_id}/sessions")
def get_user_sessions_admin(
    user_id: int,
    role: str = Query("student", enum=["student", "tutor"]),
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get detailed sessions for a user including attendance and reports"""
    from services.admin_session_service import AdminSessionService
    return AdminSessionService.get_user_sessions_detailed(db, user_id, role)

@app.get("/admin/profiles/{profile_id}/sessions")
def get_profile_sessions_admin(
    profile_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get detailed sessions for a student profile (for managed children)"""
    from services.admin_session_service import AdminSessionService
    return AdminSessionService.get_profile_sessions_detailed(db, profile_id)

@app.get("/admin/reports")
def get_all_reports_admin(
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    return AdminService.get_all_reports(db)

@app.get("/admin/settings")
def get_settings_admin(
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    return AdminService.get_settings(db)

@app.post("/admin/settings/{key}")
def update_setting_admin(
    key: str,
    value: str = Query(...),
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    AdminService.update_setting(db, key, value)
    return {"message": f"Setting {key} updated"}
