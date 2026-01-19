from sqlalchemy.orm import Session
from database.models import User, UserRole, StudentProfile, TutorProfile, ParentProfile, Session as TSession, Report, Enrollment, Attendance, AuditLog
from datetime import datetime
from typing import List, Dict, Any, Optional

class AdminCRUDService:
    """Advanced CRUD operations for admin dashboard"""
    
    # ==================== STUDENT OPERATIONS ====================
    @staticmethod
    def get_student_detail(db: Session, student_profile_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive student details including parent, sessions, and attendance"""
        profile = db.query(StudentProfile).filter(StudentProfile.id == student_profile_id).first()
        if not profile:
            return None
        
        # Get parent info if exists
        parent_info = None
        if profile.parent_id:
            parent = db.query(User).filter(User.id == profile.parent_id).first()
            if parent:
                parent_profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent.id).first()
                parent_info = {
                    "id": parent.id,
                    "name": parent.full_name,
                    "phone": parent.phone,
                    "occupation": parent_profile.occupation if parent_profile else None
                }
        
        # Get enrollments
        enrollments = db.query(Enrollment).filter(Enrollment.student_profile_id == profile.id).all()
        tutors = []
        for enr in enrollments:
            tutor = db.query(User).filter(User.id == enr.tutor_user_id).first()
            if tutor:
                tutors.append({
                    "id": tutor.id,
                    "name": tutor.full_name,
                    "enrolled_date": enr.start_date
                })
        
        # Get sessions with attendance
        sessions = db.query(TSession).filter(TSession.student_profile_id == profile.id).order_by(TSession.scheduled_at.desc()).limit(20).all()
        session_list = []
        for sess in sessions:
            tutor = db.query(User).filter(User.id == sess.tutor_id).first()
            attendance = db.query(Attendance).filter(
                Attendance.session_id == sess.id,
                Attendance.student_profile_id == profile.id
            ).first()
            
            session_list.append({
                "id": sess.id,
                "topic": sess.topic,
                "tutor": tutor.full_name if tutor else "Unknown",
                "scheduled_at": sess.scheduled_at,
                "duration": sess.duration_minutes,
                "attendance": attendance.status if attendance else None
            })
        
        return {
            "id": profile.id,
            "full_name": profile.full_name,
            "grade": profile.grade,
            "school": profile.school,
            "age": profile.age,
            "is_managed": profile.parent_id is not None,
            "parent": parent_info,
            "enrolled_tutors": tutors,
            "sessions": session_list,
            "total_sessions": len(sessions)
        }
    
    @staticmethod
    def update_student(db: Session, student_profile_id: int, data: Dict[str, Any]) -> bool:
        """Update student profile"""
        profile = db.query(StudentProfile).filter(StudentProfile.id == student_profile_id).first()
        if not profile:
            return False
        
        if "full_name" in data:
            profile.full_name = data["full_name"]
        if "grade" in data:
            profile.grade = data["grade"]
        if "school" in data:
            profile.school = data["school"]
        if "age" in data:
            profile.age = data["age"]
        
        db.commit()
        
        # Log the action
        AdminCRUDService._log_action(db, "UPDATE", "StudentProfile", student_profile_id, f"Updated student: {profile.full_name}")
        return True
    
    @staticmethod
    def delete_student(db: Session, student_profile_id: int, admin_id: int) -> bool:
        """Soft delete student profile"""
        profile = db.query(StudentProfile).filter(StudentProfile.id == student_profile_id).first()
        if not profile:
            return False
        
        student_name = profile.full_name
        
        # Delete related records
        db.query(Enrollment).filter(Enrollment.student_profile_id == student_profile_id).delete()
        db.query(Attendance).filter(Attendance.student_profile_id == student_profile_id).delete()
        # Sessions remain for historical purposes but could be marked
        
        db.delete(profile)
        db.commit()
        
        AdminCRUDService._log_action(db, "DELETE", "StudentProfile", student_profile_id, f"Deleted student: {student_name}", admin_id)
        return True
    
    # ==================== TUTOR OPERATIONS ====================
    @staticmethod
    def get_tutor_detail(db: Session, tutor_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive tutor details"""
        user = db.query(User).filter(User.id == tutor_id).first()
        if not user:
            return None
        
        profile = db.query(TutorProfile).filter(TutorProfile.user_id == tutor_id).first()
        if not profile:
            return None
        
        # Get enrolled students
        enrollments = db.query(Enrollment).filter(Enrollment.tutor_user_id == tutor_id).all()
        students = []
        for enr in enrollments:
            student_profile = db.query(StudentProfile).filter(StudentProfile.id == enr.student_profile_id).first()
            if student_profile:
                students.append({
                    "id": student_profile.id,
                    "name": student_profile.full_name,
                    "grade": student_profile.grade,
                    "enrolled_date": enr.start_date
                })
        
        # Get sessions
        sessions = db.query(TSession).filter(TSession.tutor_id == tutor_id).order_by(TSession.scheduled_at.desc()).limit(20).all()
        session_list = []
        for sess in sessions:
            student = db.query(StudentProfile).filter(StudentProfile.id == sess.student_profile_id).first()
            report = db.query(Report).filter(Report.session_id == sess.id).first()
            
            session_list.append({
                "id": sess.id,
                "topic": sess.topic,
                "student": student.full_name if student else "Unknown",
                "scheduled_at": sess.scheduled_at,
                "duration": sess.duration_minutes,
                "has_report": report is not None,
                "report_score": report.performance_score if report else None
            })
        
        return {
            "id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "telegram_id": user.telegram_id,
            "subjects": profile.subjects,
            "education": profile.education,
            "experience_years": profile.experience_years,
            "verified": profile.verified,
            "enrolled_students": students,
            "sessions": session_list,
            "total_students": len(students),
            "total_sessions": len(sessions)
        }
    
    @staticmethod
    def update_tutor(db: Session, tutor_id: int, data: Dict[str, Any], admin_id: int) -> bool:
        """Update tutor profile"""
        profile = db.query(TutorProfile).filter(TutorProfile.user_id == tutor_id).first()
        if not profile:
            return False
        
        if "subjects" in data:
            profile.subjects = data["subjects"]
        if "education" in data:
            profile.education = data["education"]
        if "experience_years" in data:
            profile.experience_years = data["experience_years"]
        if "verified" in data:
            profile.verified = data["verified"]
        
        db.commit()
        
        user = db.query(User).filter(User.id == tutor_id).first()
        AdminCRUDService._log_action(db, "UPDATE", "TutorProfile", tutor_id, f"Updated tutor: {user.full_name if user else tutor_id}", admin_id)
        return True
    
    # ==================== PARENT OPERATIONS ====================
    @staticmethod
    def get_parent_detail(db: Session, parent_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive parent details"""
        user = db.query(User).filter(User.id == parent_id).first()
        if not user:
            return None
        
        profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
        if not profile:
            return None
        
        # Get all children
        children = db.query(StudentProfile).filter(StudentProfile.parent_id == parent_id).all()
        children_list = []
        for child in children:
            # Get child's sessions and reports
            sessions = db.query(TSession).filter(TSession.student_profile_id == child.id).count()
            reports = db.query(Report).join(TSession).filter(TSession.student_profile_id == child.id).count()
            
            children_list.append({
                "id": child.id,
                "name": child.full_name,
                "grade": child.grade,
                "school": child.school,
                "total_sessions": sessions,
                "total_reports": reports
            })
        
        return {
            "id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "telegram_id": user.telegram_id,
            "occupation": profile.occupation,
            "last_report_sent": profile.last_report_sent_at,
            "children": children_list,
            "total_children": len(children_list)
        }
    
    # ==================== SESSION & ATTENDANCE OPERATIONS ====================
    @staticmethod
    def get_session_detail(db: Session, session_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed session information"""
        session = db.query(TSession).filter(TSession.id == session_id).first()
        if not session:
            return None
        
        tutor = db.query(User).filter(User.id == session.tutor_id).first()
        student = db.query(StudentProfile).filter(StudentProfile.id == session.student_profile_id).first()
        attendance = db.query(Attendance).filter(Attendance.session_id == session_id).first()
        report = db.query(Report).filter(Report.session_id == session_id).first()
        
        return {
            "id": session.id,
            "topic": session.topic,
            "scheduled_at": session.scheduled_at,
            "duration_minutes": session.duration_minutes,
            "tutor": {
                "id": tutor.id if tutor else None,
                "name": tutor.full_name if tutor else "Unknown"
            },
            "student": {
                "id": student.id if student else None,
                "name": student.full_name if student else "Unknown",
                "grade": student.grade if student else None
            },
            "attendance": {
                "status": attendance.status if attendance else None,
                "id": attendance.id if attendance else None
            },
            "report": {
                "id": report.id if report else None,
                "content": report.content if report else None,
                "score": report.performance_score if report else None,
                "created_at": report.created_at if report else None
            } if report else None
        }
    
    @staticmethod
    def update_attendance(db: Session, session_id: int, student_profile_id: int, status: str, admin_id: int) -> bool:
        """Update or create attendance record"""
        attendance = db.query(Attendance).filter(
            Attendance.session_id == session_id,
            Attendance.student_profile_id == student_profile_id
        ).first()
        
        if attendance:
            attendance.status = status
        else:
            attendance = Attendance(
                session_id=session_id,
                student_profile_id=student_profile_id,
                status=status
            )
            db.add(attendance)
        
        db.commit()
        AdminCRUDService._log_action(db, "UPDATE", "Attendance", session_id, f"Set attendance to {status}", admin_id)
        return True
    
    # ==================== AUDIT LOG ====================
    @staticmethod
    def get_audit_logs(db: Session, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit logs"""
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        result = []
        for log in logs:
            admin = db.query(User).filter(User.id == log.admin_id).first()
            result.append({
                "id": log.id,
                "admin": admin.full_name if admin else "System",
                "action": log.action,
                "entity": log.entity,
                "entity_id": log.entity_id,
                "timestamp": log.timestamp
            })
        
        return result
    
    @staticmethod
    def _log_action(db: Session, action: str, entity: str, entity_id: int, description: str = None, admin_id: int = None):
        """Internal method to log admin actions"""
        log = AuditLog(
            admin_id=admin_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()
    
    # ==================== STATISTICS ====================
    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        total_students = db.query(StudentProfile).count()
        total_tutors = db.query(TutorProfile).count()
        total_parents = db.query(ParentProfile).count()
        total_sessions = db.query(TSession).count()
        total_reports = db.query(Report).count()
        
        # Active enrollments
        active_enrollments = db.query(Enrollment).filter(Enrollment.active == True).count()
        
        # Verified vs unverified tutors
        verified_tutors = db.query(TutorProfile).filter(TutorProfile.verified == True).count()
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_sessions = db.query(TSession).filter(TSession.scheduled_at >= week_ago).count()
        recent_reports = db.query(Report).filter(Report.created_at >= week_ago).count()
        
        return {
            "total_students": total_students,
            "total_tutors": total_tutors,
            "total_parents": total_parents,
            "total_sessions": total_sessions,
            "total_reports": total_reports,
            "active_enrollments": active_enrollments,
            "verified_tutors": verified_tutors,
            "unverified_tutors": total_tutors - verified_tutors,
            "recent_sessions_7d": recent_sessions,
            "recent_reports_7d": recent_reports
        }
