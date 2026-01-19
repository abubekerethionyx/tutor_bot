from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from database.db import SessionLocal
from services.user_service import UserService
from services.session_service import SessionService
from bot.states.registration import RegistrationStates
from bot.keyboards.common import get_role_keyboard, get_main_menu
from database.models import User, StudentProfile, Enrollment

router = Router()

@router.message(F.text == "Back", StateFilter("*"))
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    db.close()
    
    if user:
        roles = [r.role for r in user.roles]
        await message.answer("Main Menu:", reply_markup=get_main_menu(roles))
    else:
        await message.answer("Please register:", reply_markup=get_role_keyboard())

@router.message(F.text.startswith("Register as "))
async def register_role_handler(message: types.Message, state: FSMContext):
    new_role = message.text.replace("Register as ", "").lower()
    await state.update_data(role=new_role)
    
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    db.close()
    
    if user:
        # User exists, skip name/phone and go to role-specific questions
        await state.update_data(full_name=user.full_name, phone=user.phone)
        if new_role == "student":
            await message.answer("Which grade are you in?", reply_markup=types.ReplyKeyboardRemove())
            await state.set_state(RegistrationStates.waiting_for_grade)
        elif new_role == "tutor":
            await message.answer("Which subjects do you teach?", reply_markup=types.ReplyKeyboardRemove())
            await state.set_state(RegistrationStates.waiting_for_subjects)
        elif new_role == "parent":
            await message.answer("What is your occupation?", reply_markup=types.ReplyKeyboardRemove())
            await state.set_state(RegistrationStates.waiting_for_occupation)
    else:
        # New user flow
        await message.answer(f"Great! You are registering as a {new_role.capitalize()}. What is your full name?", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(RegistrationStates.waiting_for_full_name)

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
        await message.answer(
            f"Welcome back, {user.full_name}!",
            reply_markup=get_main_menu(roles)
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
                 
                 enrollments = SessionService.get_enrollments_for_student_profile(db, student_profile.id)
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
                 
                 enrollments = SessionService.get_enrollments_for_tutor(db, user.id)
                 response_parts.append(f"Total Students: {len(enrollments)}")
                 
                 sessions = SessionService.get_user_sessions(db, user.id, "tutor")
                 response_parts.append(f"Total Sessions: {len(sessions)}")

        if "parent" in roles_list:
             parent_profile = UserService.get_parent_profile(db, user.id)
             if parent_profile:
                 response_parts.append(f"\n👪 *Parent Info*")
                 response_parts.append(f"Occupation: {parent_profile.occupation}")
                 
                 children = UserService.get_managed_children(db, user.id)
                 response_parts.append(f"Managed Children: {len(children)}")

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
    
    user = UserService.get_user_by_telegram_id(db, callback.from_user.id)
    if not user:
        await callback.answer("Please register first!", show_alert=True)
        db.close()
        return

    roles = [r.role for r in user.roles]
    
    if "parent" in roles:
        children = UserService.get_managed_children(db, user.id)
        if not children:
            await callback.answer("Register your child first using 'Add New Student'.", show_alert=True)
            db.close()
            return

        builder = InlineKeyboardBuilder()
        for child in children:
            builder.button(text=child.full_name, callback_data=f"childenroll_{tutor_id}_{child.id}")
        builder.adjust(1)
        
        await callback.message.answer("Which child are you enrolling?", reply_markup=builder.as_markup())
        await callback.answer()
        db.close()
        return

    # User is a student
    profile = UserService.get_student_profile(db, user.id)
    if not profile:
        await callback.answer("You must be registered as a student to enroll.", show_alert=True)
        db.close()
        return

    try:
        SessionService.enroll_student(db, profile.id, tutor_id)
        await callback.message.answer("🎉 Successfully enrolled! The tutor will contact you soon.")
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)
    finally:
        db.close()

@router.callback_query(F.data.startswith("childenroll_"))
async def handle_child_enrollment(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    tutor_id = int(parts[1])
    child_profile_id = int(parts[2])
    
    db = SessionLocal()
    try:
        SessionService.enroll_student(db, child_profile_id, tutor_id)
        child = db.query(StudentProfile).filter(StudentProfile.id == child_profile_id).first()
        child_name = child.full_name if child else "your child"
        
        await callback.message.edit_text(f"🎉 Successfully enrolled **{child_name}** with the tutor!", parse_mode="Markdown")
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
        roles = [r.role for r in user.roles]
        primary_role = "tutor" if "tutor" in roles else ("parent" if "parent" in roles else "student")
        
        if primary_role == "parent":
            children = UserService.get_managed_children(db, user.id)
            if not children:
                await message.answer("No children linked.")
                db.close()
                return
            
            response = "📅 *Family Sessions:*\n\n"
            found = False
            for child in children:
                sessions = SessionService.get_profile_sessions(db, child.id)
                if sessions:
                    found = True
                    response += f"👶 *{child.full_name}:*\n"
                    for sess in sessions:
                        tutor = db.query(User).filter(User.id == sess.tutor_id).first()
                        tutor_name = tutor.full_name if tutor else "Unknown"
                        response += f"• {sess.topic} w/ {tutor_name} ({sess.scheduled_at.strftime('%Y-%m-%d %H:%M')})\n"
                    response += "\n"
            
            if not found:
                await message.answer("No upcoming sessions for your family.")
            else:
                await message.answer(response, parse_mode="Markdown")
        else:
            sessions = SessionService.get_user_sessions(db, user.id, primary_role)
            if not sessions:
                await message.answer("You have no upcoming sessions.")
            else:
                response = "📅 *Your Sessions:*\n\n"
                for sess in sessions:
                    with_name = ""
                    if primary_role == "tutor":
                        with_name = sess.student_profile.full_name if sess.student_profile else "Unknown"
                    else:
                        tutor = db.query(User).filter(User.id == sess.tutor_id).first()
                        with_name = tutor.full_name if tutor else "Unknown"
                    
                    label = "Student" if primary_role == "tutor" else "Tutor"
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

@router.message(F.text == "Help")
async def help_handler(message: types.Message):
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, message.from_user.id)
    
    if not user:
        # Generic help for unregistered users
        help_text = (
            "❓ *Welcome to Tutormula!*\n\n"
            "To get started, please use /start to register as a Student, Tutor, or Parent.\n\n"
            "📞 *Support*: Contact @support_handle for assistance."
        )
        await message.answer(help_text, parse_mode="Markdown")
        db.close()
        return
    
    roles = [r.role for r in user.roles]
    
    # Build role-specific help
    help_sections = []
    
    help_sections.append("❓ *Tutormula Help Guide*\n")
    
    if "student" in roles:
        help_sections.append(
            "🎓 *For Students:*\n"
            "• *Search Tutors*: Browse available tutors and enroll with them\n"
            "• *My Sessions*: View your upcoming and past sessions\n"
            "• *My Attendance*: Check your attendance record\n"
            "• *Profile*: View your academic information and stats\n"
            "• *Create Session*: Schedule a new session with your enrolled tutors\n"
        )
    
    if "tutor" in roles:
        help_sections.append(
            "👨‍🏫 *For Tutors:*\n"
            "• *My Students*: View all students enrolled with you\n"
            "• *Create Session*: Schedule sessions with your students\n"
            "• *Create Report*: Write performance reports after sessions\n"
            "• *My Sessions*: Manage your teaching schedule\n"
            "• *Profile*: View your professional details and verification status\n"
        )
    
    if "parent" in roles:
        help_sections.append(
            "👪 *For Parents:*\n"
            "• *Add New Student*: Register your child directly (they don't need their own Telegram)\n"
            "• *Link Child*: Connect an existing student account to your parent portal\n"
            "• *My Children*: View all your registered children\n"
            "• *Child Reports*: Access performance reports for each child\n"
            "• *Create Session*: Schedule sessions for your children\n"
            "• *Search Tutors*: Find and enroll tutors for your children\n"
        )
    
    help_sections.append(
        "\n🔧 *General Features:*\n"
        "• *Back*: Return to the main menu from any screen\n"
        "• *Profile*: View your complete account information\n"
        "• *Help*: Show this help message\n"
    )
    
    help_sections.append(
        "\n💡 *Tips:*\n"
        "• All your data is securely stored and accessible anytime\n"
        "• Parents can manage multiple children from one account\n"
        "• Reports are automatically sent to parents\n"
    )
    
    help_sections.append(
        "\n📞 *Support*: If you encounter any issues, contact @support_handle"
    )
    
    help_text = "\n".join(help_sections)
    await message.answer(help_text, parse_mode="Markdown")
    db.close()
