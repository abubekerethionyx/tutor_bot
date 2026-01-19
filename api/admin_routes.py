from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from database.db import SessionLocal
from services.admin_crud_service import AdminCRUDService
from api.auth import verify_admin

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== DASHBOARD STATS ====================
@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get comprehensive dashboard statistics"""
    return AdminCRUDService.get_dashboard_stats(db)

# ==================== STUDENT CRUD ====================
@router.get("/students/{student_id}/detail")
def get_student_detail(
    student_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get detailed student information"""
    result = AdminCRUDService.get_student_detail(db, student_id)
    if not result:
        raise HTTPException(status_code=404, detail="Student not found")
    return result

@router.put("/students/{student_id}")
def update_student(
    student_id: int,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Update student profile"""
    success = AdminCRUDService.update_student(db, student_id, data)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student updated successfully"}

@router.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    admin_id: int = Query(1),  # TODO: Get from auth
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Delete student profile"""
    success = AdminCRUDService.delete_student(db, student_id, admin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}

# ==================== TUTOR CRUD ====================
@router.get("/tutors/{tutor_id}/detail")
def get_tutor_detail(
    tutor_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get detailed tutor information"""
    result = AdminCRUDService.get_tutor_detail(db, tutor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Tutor not found")
    return result

@router.put("/tutors/{tutor_id}")
def update_tutor(
    tutor_id: int,
    data: Dict[str, Any],
    admin_id: int = Query(1),
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Update tutor profile"""
    success = AdminCRUDService.update_tutor(db, tutor_id, data, admin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tutor not found")
    return {"message": "Tutor updated successfully"}

# ==================== PARENT CRUD ====================
@router.get("/parents/{parent_id}/detail")
def get_parent_detail(
    parent_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get detailed parent information"""
    result = AdminCRUDService.get_parent_detail(db, parent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Parent not found")
    return result

# ==================== SESSION CRUD ====================
@router.get("/sessions/{session_id}/detail")
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get detailed session information"""
    result = AdminCRUDService.get_session_detail(db, session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result

@router.put("/sessions/{session_id}/attendance")
def update_session_attendance(
    session_id: int,
    student_profile_id: int = Query(...),
    status: str = Query(..., pattern="^(present|absent|late)$"),
    admin_id: int = Query(1),
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Update attendance for a session"""
    success = AdminCRUDService.update_attendance(db, session_id, student_profile_id, status, admin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": f"Attendance marked as {status}"}

# ==================== AUDIT LOGS ====================
@router.get("/audit-logs")
def get_audit_logs(
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get recent audit logs"""
    return AdminCRUDService.get_audit_logs(db, limit)
