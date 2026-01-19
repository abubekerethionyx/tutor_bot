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
from config import settings
from typing import List, Optional

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tutormula API")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_admin(x_admin_token: str = Header(...)):
    if x_admin_token != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return x_admin_token

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
        session.student_id, 
        session.scheduled_at, 
        session.duration_minutes, 
        session.topic
    )

@app.get("/sessions/user/{user_id}", response_model=List[schemas.SessionResponse])
def get_user_sessions(user_id: int, role: str = Query("student"), db: Session = Depends(get_db)):
    return SessionService.get_user_sessions(db, user_id, role)

# --- Admin Routes ---

@app.get("/admin/students", response_model=List[schemas.AdminStudentDetail])
def get_admin_students(db: Session = Depends(get_db), admin: str = Depends(verify_admin)):
    return AdminService.get_student_details(db)

@app.get("/admin/tutors", response_model=List[schemas.AdminTutorDetail])
def get_admin_tutors(db: Session = Depends(get_db), admin: str = Depends(verify_admin)):
    return AdminService.get_tutor_details(db)

@app.get("/admin/reports/sessions", response_model=schemas.SessionReportSummary)
def get_admin_session_report(
    period: str = Query("daily", enum=["daily", "weekly", "monthly"]),
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    return AdminService.get_session_stats(db, period)
