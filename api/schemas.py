from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    telegram_id: int
    full_name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class TutorProfileResponse(BaseModel):
    subjects: str
    education: str
    experience_years: int
    verified: bool
    class Config:
        from_attributes = True

class StudentProfileResponse(BaseModel):
    grade: str
    school: str
    age: int
    class Config:
        from_attributes = True

class TutorSearchResponse(UserResponse):
    tutor_profile: Optional[TutorProfileResponse] = None

class EnrollmentCreate(BaseModel):
    student_id: int
    tutor_id: int

class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    tutor_id: int
    start_date: datetime
    active: bool
    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    tutor_id: int
    student_id: int
    scheduled_at: datetime
    duration_minutes: int
    topic: str

class SessionResponse(BaseModel):
    id: int
    tutor_id: int
    student_id: int
    tutor_name: Optional[str] = None
    student_name: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int
    topic: str
    class Config:
        from_attributes = True

# --- Admin Schemas ---

class AdminStudentDetail(BaseModel):
    id: int
    full_name: str
    phone: Optional[str]
    telegram_id: int
    grade: str
    school: str
    age: int
    created_at: datetime

class AdminTutorDetail(BaseModel):
    id: int
    full_name: str
    phone: Optional[str]
    telegram_id: int
    subjects: str
    education: str
    experience_years: int
    verified: bool
    created_at: datetime

class SessionReportSummary(BaseModel):
    period: str
    total_sessions: int
    total_duration_minutes: int
    total_reports: int
    average_performance_score: float
    sessions: List[SessionResponse]
