import hashlib
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz
from app.models.session_models import (
    SessionConfig, SessionInfo, StudentProgress, LiveStats,
    SessionActivity, QRCodeInfo
)
from app.services.database_service import get_database_service
from app.models.database_models import Session, Student

class SessionService:
    def __init__(self):
        self.kst = pytz.timezone('Asia/Seoul')
        self.db_service = get_database_service()

    def get_korea_time(self):
        """Get current time in Korea Standard Time"""
        utc_now = datetime.now(pytz.UTC)
        return utc_now.astimezone(self.kst)

    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = str(int(self.get_korea_time().timestamp()))[-8:]
        random_part = str(uuid.uuid4()).replace('-', '')[:6].upper()
        checksum = hashlib.md5((timestamp + random_part).encode()).hexdigest()[:3].upper()
        return f"{timestamp}{random_part}{checksum}"

    def generate_browser_fingerprint(self, request_headers: Dict[str, str]) -> str:
        """Generate browser fingerprint from request headers (for teacher identification only)"""
        user_agent = request_headers.get('user-agent', '')
        accept_language = request_headers.get('accept-language', '')
        fingerprint_data = f"{user_agent}|{accept_language}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]

    def generate_student_token(self) -> str:
        """Generate unique student session token"""
        return secrets.token_urlsafe(16)

    async def create_session(self, config: SessionConfig, teacher_fingerprint: str, base_url: str) -> Dict[str, Any]:
        """Create new session"""
        session_id = self.generate_session_id()
        now = self.get_korea_time()
        expires_at = now + timedelta(hours=2)

        session_data = {
            'id': session_id,
            'teacher_fingerprint': teacher_fingerprint,
            'config': config.dict(),
            'status': 'active',
            'created_at': now.isoformat(),
            'expires_at': expires_at.isoformat(),
            'last_activity': now.isoformat(),
            'ended_at': None,
            'deleted_at': None
        }

        # Save to database
        try:
            await self.db_service.save_session(session_id, session_data)
            print(f"✅ Session {session_id} saved to database")
        except Exception as e:
            print(f"❌ Failed to save session {session_id}: {e}")
            raise

        session_url = f"{base_url}/s/{session_id}"

        return {
            'session_id': session_id,
            'session_data': session_data,
            'session_url': session_url
        }

    async def get_teacher_sessions(self, teacher_fingerprint: str) -> List[Dict[str, Any]]:
        """Get all sessions for a teacher"""
        current_korea_time = self.get_korea_time()

        # Get sessions from database
        db_sessions = await self.db_service.get_sessions_by_teacher(teacher_fingerprint)

        teacher_sessions = []
        for db_session in db_sessions:
            # Get student count
            students = await self.db_service.get_students_by_session(db_session.id)

            # Calculate duration
            created_at = db_session.created_at
            if created_at.tzinfo is None:
                created_at = self.kst.localize(created_at)
            elif created_at.tzinfo != self.kst:
                created_at = created_at.astimezone(self.kst)

            duration_minutes = int((current_korea_time - created_at).total_seconds() / 60)

            # Get live stats
            live_stats = await self.db_service._calculate_live_stats(db_session.id)

            session_dict = {
                'id': db_session.id,
                'teacher_fingerprint': db_session.teacher.fingerprint,
                'config': {
                    'title': db_session.title,
                    'topic': db_session.topic,
                    'description': db_session.description,
                    'difficulty': db_session.difficulty,
                    'show_score': db_session.show_score,
                    'time_limit': db_session.time_limit,
                    'max_students': db_session.max_students
                },
                'status': db_session.status,
                'created_at': db_session.created_at.isoformat(),
                'expires_at': db_session.expires_at.isoformat(),
                'last_activity': db_session.last_activity.isoformat() if db_session.last_activity else db_session.created_at.isoformat(),
                'ended_at': db_session.ended_at.isoformat() if db_session.ended_at else None,
                'deleted_at': None,
                'students_count': len(students),
                'duration_minutes': max(0, duration_minutes),
                'students': {},
                'live_stats': live_stats,
                'events': []
            }

            teacher_sessions.append(session_dict)

        return teacher_sessions

    async def get_session_details(self, session_id: str, teacher_fingerprint: str) -> Optional[Dict[str, Any]]:
        """Get detailed session information for monitoring"""
        # Get session from database
        db_session = await self.db_service.get_session_by_id(session_id)

        if not db_session or db_session.teacher.fingerprint != teacher_fingerprint:
            return None

        # Get students
        db_students = await self.db_service.get_students_by_session(session_id)

        # Calculate session duration
        current_korea_time = self.get_korea_time()
        created_at = db_session.created_at
        if created_at.tzinfo is None:
            created_at = self.kst.localize(created_at)
        elif created_at.tzinfo != self.kst:
            created_at = created_at.astimezone(self.kst)

        duration_minutes = int((current_korea_time - created_at).total_seconds() / 60)

        # Get live stats
        live_stats = await self.db_service._calculate_live_stats(session_id)

        session_dict = {
            'id': db_session.id,
            'teacher_fingerprint': db_session.teacher.fingerprint,
            'config': {
                'title': db_session.title,
                'topic': db_session.topic,
                'description': db_session.description,
                'difficulty': db_session.difficulty,
                'show_score': db_session.show_score,
                'time_limit': db_session.time_limit,
                'max_students': db_session.max_students
            },
            'status': db_session.status,
            'created_at': db_session.created_at.isoformat(),
            'expires_at': db_session.expires_at.isoformat(),
            'last_activity': db_session.last_activity.isoformat() if db_session.last_activity else db_session.created_at.isoformat(),
            'ended_at': db_session.ended_at.isoformat() if db_session.ended_at else None,
            'duration_minutes': max(0, duration_minutes),
            'live_stats': live_stats
        }

        # Calculate student progress
        students = []
        for db_student in db_students:
            progress = await self._calculate_student_progress(db_student)
            students.append(progress)

        print(f"🔍 Session {session_id} has {len(students)} students")

        return {
            'session': session_dict,
            'students': students
        }

    async def join_session(self, session_id: str, student_name: str = "익명", student_token: str = None) -> Optional[Dict[str, Any]]:
        """Student joins a session"""
        # Get session from database
        db_session = await self.db_service.get_session_by_id(session_id)

        if not db_session:
            return None

        # Check for existing student by token first
        existing_student = None
        if student_token:
            existing_student = await self.db_service.get_student_by_token(session_id, student_token)
            if existing_student:
                print(f"🔄 Returning student detected by TOKEN: {existing_student.id}")

        # If no token match, check by name
        if not existing_student:
            existing_student = await self.db_service.get_student_by_name(session_id, student_name)
            if existing_student:
                print(f"🔄 Returning student detected by NAME: {existing_student.id}")

        if existing_student:
            # Update last active
            await self.db_service.update_student_last_active(existing_student.id)

            return {
                'student_id': existing_student.id,
                'student_token': existing_student.token,
                'session_config': SessionConfig(
                    title=db_session.title,
                    topic=db_session.topic,
                    description=db_session.description,
                    difficulty=db_session.difficulty,
                    show_score=db_session.show_score,
                    time_limit=db_session.time_limit,
                    max_students=db_session.max_students
                ),
                'session_status': db_session.status,
                'is_returning': True,
                'current_score': existing_student.current_score
            }

        # Create new student
        student_id = str(uuid.uuid4())
        new_student_token = self.generate_student_token()

        print(f"✨ Creating new student: {student_id} with name '{student_name}'")

        new_student = await self.db_service.create_student(
            student_id=student_id,
            session_id=session_id,
            name=student_name,
            token=new_student_token
        )

        if not new_student:
            return None

        return {
            'student_id': student_id,
            'student_token': new_student_token,
            'session_config': SessionConfig(
                title=db_session.title,
                topic=db_session.topic,
                description=db_session.description,
                difficulty=db_session.difficulty,
                show_score=db_session.show_score,
                time_limit=db_session.time_limit,
                max_students=db_session.max_students
            ),
            'session_status': db_session.status,
            'is_returning': False,
            'current_score': 0
        }

    async def update_student_progress(
        self,
        session_id: str,
        student_id: str,
        understanding_score: int,
        dimensions: Dict[str, int],
        is_completed: bool = False,
        last_message: str = ""
    ):
        """Update student progress (message should be saved separately by caller)"""
        # Update progress in database
        success = await self.db_service.update_student_progress(
            student_id=student_id,
            understanding_score=understanding_score,
            dimensions=dimensions,
            is_completed=is_completed
        )

        # Note: Messages are saved by the API endpoint to avoid duplicate saves
        # The last_message parameter is kept for compatibility but not used

        return success

    async def end_session(self, session_id: str, teacher_fingerprint: str) -> Optional[Dict[str, Any]]:
        """Delete a session (simplified from end)"""
        return await self.delete_session(session_id, teacher_fingerprint)

    async def delete_session(self, session_id: str, teacher_fingerprint: str) -> bool:
        """Soft delete a session"""
        db_session = await self.db_service.get_session_by_id(session_id)

        if not db_session or db_session.teacher.fingerprint != teacher_fingerprint:
            return False

        # Soft delete
        success = await self.db_service.delete_session(session_id)

        if success:
            print(f"✅ Soft deleted session {session_id}")

        return success

    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        # This would need a new method in database_service to find and soft-delete expired sessions
        # For now, we'll skip this as it requires querying all sessions
        print("🔄 Cleanup expired sessions - skipped (not critical for DB-only architecture)")

    async def _calculate_student_progress(self, student: Student) -> Dict[str, Any]:
        """Calculate student progress for display"""
        now = self.get_korea_time()

        # Parse timestamps
        joined_at = student.joined_at
        if joined_at.tzinfo is None:
            joined_at = self.kst.localize(joined_at)
        elif joined_at.tzinfo != self.kst:
            joined_at = joined_at.astimezone(self.kst)

        last_active = student.last_active
        if last_active.tzinfo is None:
            last_active = self.kst.localize(last_active)
        elif last_active.tzinfo != self.kst:
            last_active = last_active.astimezone(self.kst)

        time_spent = int((now - joined_at).total_seconds() / 60)
        minutes_since_last_activity = int((now - last_active).total_seconds() / 60)

        # Calculate progress percentage
        avg_dimension = (student.depth_score + student.breadth_score +
                        student.application_score + student.metacognition_score +
                        student.engagement_score) / 5.0
        progress_percentage = min(100, int(avg_dimension))

        # Get last message
        messages = await self.db_service.get_student_messages(student.session_id, student.id)
        last_message = messages[0]['content'] if messages else None

        return {
            'student_id': student.id,
            'student_name': student.name,
            'latest_score': student.current_score,
            'message_count': student.conversation_turns,  # Use conversation_turns from students table
            'joined_at': joined_at,
            'last_activity': last_active,
            'minutes_since_last_activity': minutes_since_last_activity,
            'time_spent': time_spent,
            'progress_percentage': progress_percentage,
            'conversation_turns': student.conversation_turns,
            'current_dimensions': {
                'depth': student.depth_score,
                'breadth': student.breadth_score,
                'application': student.application_score,
                'metacognition': student.metacognition_score,
                'engagement': student.engagement_score
            },
            'last_message': last_message,
            'is_completed': student.is_completed
        }


# Singleton instance
_session_service = SessionService()

def get_session_service() -> SessionService:
    return _session_service
