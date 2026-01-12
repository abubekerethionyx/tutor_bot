from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.db import SessionLocal
from services.user_service import UserService
from bot.states.registration import RegistrationStates
from bot.keyboards.common import get_role_keyboard, get_main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    db.close()

    if not user:
        await message.answer(
            f"Welcome to Tutormula! 🎓\n\nPlease select your role to begin registration:",
            reply_markup=get_role_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_role)
    else:
        roles = [r.role for r in user.roles]
        role = "tutor" if "tutor" in roles else ("parent" if "parent" in roles else "student")
        await message.answer(
            f"Welcome back, {user.full_name}!",
            reply_markup=get_main_menu(role)
        )

@router.message(F.text == "Profile")
async def profile_handler(message: types.Message):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    if user:
        response_parts = [
            f"👤 *Profile Details*",
            f"",
            f"Name: {user.full_name}"
        ]
        
        if user.phone:
            response_parts.append(f"Phone: {user.phone}")
            
        roles_list = [r.role for r in user.roles] if user.roles else []
        roles_str = ", ".join(roles_list) if roles_list else "None"
        response_parts.append(f"Roles: {roles_str}")
        
        if "student" in roles_list:
             student_profile = UserService.get_student_profile(db, user.id)
             if student_profile:
                 response_parts.append(f"\n📚 *Student Info*")
                 response_parts.append(f"Grade: {student_profile.grade}")
                 response_parts.append(f"School: {student_profile.school}")
                 response_parts.append(f"Age: {student_profile.age}")
                 
                 from services.session_service import SessionService
                 enrollments = SessionService.get_enrollments_for_student(db, user.id)
                 response_parts.append(f"Enrolled Tutors: {len(enrollments)}")
                 
                 sessions = SessionService.get_user_sessions(db, user.id, "student")
                 response_parts.append(f"Total Sessions: {len(sessions)}")
        
        if "tutor" in roles_list:
             tutor_profile = UserService.get_tutor_profile(db, user.id)
             if tutor_profile:
                 response_parts.append(f"\n👨‍🏫 *Tutor Info*")
                 response_parts.append(f"Subjects: {tutor_profile.subjects}")
                 response_parts.append(f"Education: {tutor_profile.education}")
                 response_parts.append(f"Experience: {tutor_profile.experience_years} years")
                 status = "✅ Verified" if tutor_profile.verified else "⏳ Pending Verification"
                 response_parts.append(f"Status: {status}")
                 
                 from services.session_service import SessionService
                 enrollments = SessionService.get_enrollments_for_tutor(db, user.id)
                 response_parts.append(f"Total Students: {len(enrollments)}")
                 
                 sessions = SessionService.get_user_sessions(db, user.id, "tutor")
                 response_parts.append(f"Total Sessions: {len(sessions)}")

        if "parent" in roles_list:
             parent_profile = UserService.get_parent_profile(db, user.id)
             if parent_profile:
                 response_parts.append(f"\n👪 *Parent Info*")
                 response_parts.append(f"Occupation: {parent_profile.occupation}")

        await message.answer("\n".join(response_parts), parse_mode="Markdown")
    
    db.close()
from aiogram.utils.keyboard import InlineKeyboardBuilder

@router.message(F.text == "Search Tutors")
async def search_tutors_handler(message: types.Message):
    db = SessionLocal()
    tutors = UserService.search_tutors(db)
    
    if not tutors:
        await message.answer("No tutors available at the moment.")
    else:
        await message.answer("🔍 *Available Tutors:*", parse_mode="Markdown")
        for tutor in tutors:
            profile = UserService.get_tutor_profile(db, tutor.id)
            if profile:
                subjects = profile.subjects
                education = profile.education
                exp = profile.experience_years
                status = "✅ Verified" if profile.verified else "⏳ Pending Verification"
                
                resp = (
                    f"👤 *{tutor.full_name}*\n"
                    f"📚 Subjects: {subjects}\n"
                    f"🎓 Education: {education}\n"
                    f"⏳ Experience: {exp} years\n"
                    f"🛡️ Status: {status}"
                )
            else:
                resp = f"👤 *{tutor.full_name}*\n📚 Subjects: Not specified"
            
            builder = InlineKeyboardBuilder()
            builder.button(text="Enroll 📝", callback_data=f"enroll_{tutor.id}")
            
            await message.answer(
                resp,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
    db.close()

@router.callback_query(F.data.startswith("enroll_"))
async def enroll_callback(callback: types.CallbackQuery):
    tutor_id = int(callback.data.split("_")[1])
    db = SessionLocal()
    
    # Get current user
    user = UserService.get_user_by_telegram_id(db, callback.from_user.id)
    if not user:
        await callback.answer("Please register first!", show_alert=True)
        db.close()
        return

    from services.session_service import SessionService
    try:
        SessionService.enroll_student(db, user.id, tutor_id)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("🎉 Successfully enrolled! The tutor will contact you soon.")
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)
    finally:
        db.close()

@router.message(F.text == "My Sessions")
async def my_sessions_handler(message: types.Message):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    if user:
        # Determine primary role for session lookup
        roles = [r.role for r in user.roles]
        role = "tutor" if "tutor" in roles else "student"
        
        from services.session_service import SessionService
        sessions = SessionService.get_user_sessions(db, user.id, role)
        
        if not sessions:
            await message.answer("You have no upcoming sessions.")
        else:
            from database.models import User
            response = "📅 *Your Sessions:*\n\n"
            for sess in sessions:
                other_user_id = sess.student_id if role == "tutor" else sess.tutor_id
                other_user = db.query(User).filter(User.id == other_user_id).first()
                with_name = other_user.full_name if other_user else "Unknown"
                
                label = "Student" if role == "tutor" else "Tutor"
                response += (
                    f"🔹 *{sess.topic}*\n"
                    f"👤 {label}: {with_name}\n"
                    f"⏰ {sess.scheduled_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"⏳ {sess.duration_minutes} min\n\n"
                )
            await message.answer(response, parse_mode="Markdown")
    else:
        await message.answer("Please register first.")
    db.close()
