import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import pytz
from app.models.session_models import (
    SessionConfig, SessionInfo, StudentProgress, LiveStats,
    SessionActivity, QRCodeInfo
)
from app.services.storage_service import get_storage_service

class SessionService:
    def __init__(self):
        # In-memory storage for active sessions (with file backup)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_students: Dict[str, Dict[str, Any]] = {}  # session_id -> {student_id -> student_data}
        self.kst = pytz.timezone('Asia/Seoul')
        self.storage_service = get_storage_service()
        self._data_loaded = False

        # Load existing data will be called when first accessed

    async def _ensure_data_loaded(self):
        """Ensure data is loaded from storage (lazy initialization)"""
        if self._data_loaded:
            return

        try:
            print("🔄 Loading persisted session data...")

            # Load sessions
            persisted_sessions = await self.storage_service.load_sessions()
            self.active_sessions.update(persisted_sessions)
            print(f"✅ Loaded {len(persisted_sessions)} sessions from storage")

            # Load students
            persisted_students = await self.storage_service.load_students()
            self.session_students.update(persisted_students)
            total_students = sum(len(session_students) for session_students in persisted_students.values())
            print(f"✅ Loaded {total_students} students from storage")

            self._data_loaded = True

        except Exception as e:
            print(f"❌ Error loading persisted data: {e}")
            self._data_loaded = True  # Mark as loaded to avoid retry loops

    def get_korea_time(self):
        """Get current time in Korea Standard Time"""
        utc_now = datetime.now(pytz.UTC)
        return utc_now.astimezone(self.kst)

    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = str(int(self.get_korea_time().timestamp()))[-8:]  # Last 8 digits
        random_part = str(uuid.uuid4()).replace('-', '')[:6].upper()
        checksum = hashlib.md5((timestamp + random_part).encode()).hexdigest()[:3].upper()
        return f"{timestamp}{random_part}{checksum}"

    def generate_browser_fingerprint(self, request_headers: Dict[str, str]) -> str:
        """Generate browser fingerprint from request headers"""
        user_agent = request_headers.get('user-agent', '')
        accept_language = request_headers.get('accept-language', '')
        fingerprint_data = f"{user_agent}|{accept_language}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]

    async def create_session(self, config: SessionConfig, teacher_fingerprint: str, base_url: str) -> Dict[str, Any]:
        """Create new session"""
        await self._ensure_data_loaded()
        session_id = self.generate_session_id()
        now = self.get_korea_time()
        expires_at = now + timedelta(hours=2)  # Sessions expire after 2 hours

        # Debug timing
        print(f"🕐 DEBUG - Current Korea time: {now}")
        print(f"🕐 DEBUG - ISO format: {now.isoformat()}")
        print(f"🕐 DEBUG - Timezone: {now.tzinfo}")

        session_data = {
            'id': session_id,
            'teacher_fingerprint': teacher_fingerprint,
            'config': config.dict(),
            'status': 'active',  # single state: active
            'created_at': now.isoformat(),  # Convert to ISO string with timezone
            'expires_at': expires_at.isoformat(),  # Convert to ISO string with timezone
            'last_activity': now.isoformat(),  # Convert to ISO string with timezone
            'students': {},
            'live_stats': {
                'current_students': 0,
                'total_joined': 0,
                'average_score': 0.0,
                'completion_rate': 0.0,
                'dimension_averages': {
                    'depth': 0.0,
                    'breadth': 0.0,
                    'application': 0.0,
                    'metacognition': 0.0,
                    'engagement': 0.0
                },
                'recent_activities': []
            },
            'events': []
        }

        self.active_sessions[session_id] = session_data
        self.session_students[session_id] = {}

        # Save to persistent storage
        try:
            await self.storage_service.save_session(session_id, session_data)
            await self.storage_service.save_session_students(session_id, {})
            print(f"💾 Session {session_id} saved to persistent storage")
        except Exception as e:
            print(f"❌ Failed to save session {session_id}: {e}")

        # Generate QR code URL
        session_url = f"{base_url}/s/{session_id}"

        return {
            'session_id': session_id,
            'session_data': session_data,
            'session_url': session_url
        }

    async def get_teacher_sessions(self, teacher_fingerprint: str) -> List[Dict[str, Any]]:
        """Get all sessions for a teacher"""
        await self._ensure_data_loaded()
        teacher_sessions = []
        current_korea_time = self.get_korea_time()
        print(f"🕐 DEBUG - get_teacher_sessions current Korea time: {current_korea_time}")

        print(f"🔍 DEBUG - Total active sessions: {len(self.active_sessions)}")
        print(f"🔍 DEBUG - Looking for fingerprint: {teacher_fingerprint}")

        for session_id, session_data in self.active_sessions.items():
            session_fingerprint = session_data['teacher_fingerprint']
            print(f"🔍 DEBUG - Session {session_id} has fingerprint: {session_fingerprint}")

            if session_data['teacher_fingerprint'] == teacher_fingerprint:
                print(f"🔍 DEBUG - MATCH! Processing session {session_id}")
                # Add calculated fields
                session_copy = session_data.copy()
                session_copy['students_count'] = len(session_data['students'])

                # Calculate session duration in minutes (server-side)
                created_at_str = session_data.get('created_at')
                if created_at_str:
                    from datetime import datetime
                    # Parse the ISO string back to datetime
                    created_at = datetime.fromisoformat(created_at_str)
                    # Ensure it's in Korean timezone
                    if created_at.tzinfo is None:
                        created_at = self.kst.localize(created_at)
                    elif created_at.tzinfo != self.kst:
                        created_at = created_at.astimezone(self.kst)

                    duration_minutes = int((current_korea_time - created_at).total_seconds() / 60)
                    session_copy['duration_minutes'] = max(0, duration_minutes)
                else:
                    session_copy['duration_minutes'] = 0

                # Debug the created_at time
                print(f"🕐 DEBUG - Session {session_id} created_at: {created_at_str} (type: {type(created_at_str)})")
                print(f"🕐 DEBUG - Session {session_id} duration: {session_copy['duration_minutes']} minutes")

                teacher_sessions.append(session_copy)

        # Sort by created_at desc
        teacher_sessions.sort(key=lambda x: x['created_at'], reverse=True)
        return teacher_sessions

    async def get_session_details(self, session_id: str, teacher_fingerprint: str) -> Optional[Dict[str, Any]]:
        """Get detailed session information for monitoring"""
        await self._ensure_data_loaded()
        session_data = self.active_sessions.get(session_id)
        if not session_data or session_data['teacher_fingerprint'] != teacher_fingerprint:
            return None

        # Add session duration to session data
        session_copy = session_data.copy()
        current_korea_time = self.get_korea_time()

        # Calculate session duration in minutes (server-side)
        created_at_str = session_data.get('created_at')
        if created_at_str:
            from datetime import datetime
            # Parse the ISO string back to datetime
            created_at = datetime.fromisoformat(created_at_str)
            # Ensure it's in Korean timezone
            if created_at.tzinfo is None:
                created_at = self.kst.localize(created_at)
            elif created_at.tzinfo != self.kst:
                created_at = created_at.astimezone(self.kst)

            duration_minutes = int((current_korea_time - created_at).total_seconds() / 60)
            session_copy['duration_minutes'] = max(0, duration_minutes)
        else:
            session_copy['duration_minutes'] = 0

        # Get student progress details
        students = []
        for student_id, student_data in self.session_students.get(session_id, {}).items():
            progress = self._calculate_student_progress(student_data)
            students.append(progress)

        return {
            'session': session_copy,
            'students': students
        }

    async def join_session(self, session_id: str, student_name: str = "익명") -> Optional[Dict[str, Any]]:
        """Student joins a session"""
        await self._ensure_data_loaded()
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return None


        # Generate student ID
        student_id = str(uuid.uuid4())
        now = self.get_korea_time()

        # Create student data
        student_data = {
            'id': student_id,
            'name': student_name,
            'session_id': session_id,
            'joined_at': now.isoformat(),  # Convert to ISO string with timezone
            'last_active': now.isoformat(),  # Convert to ISO string with timezone
            'progress': {
                'conversation_turns': 0,
                'current_score': 0,
                'dimensions': {
                    'depth': 0,
                    'breadth': 0,
                    'application': 0,
                    'metacognition': 0,
                    'engagement': 0
                },
                'is_completed': False,
                'completed_at': None
            },
            'messages': []
        }

        # Add student to session
        if session_id not in self.session_students:
            self.session_students[session_id] = {}
        self.session_students[session_id][student_id] = student_data

        # Update session stats
        session_data['live_stats']['total_joined'] += 1
        session_data['live_stats']['current_students'] = len(self.session_students[session_id])


        # Log activity
        activity = {
            'type': 'student_joined',
            'student_id': student_id,
            'student_name': student_name,
            'timestamp': now.isoformat(),  # Convert to ISO string with timezone
            'data': {'students_count': session_data['live_stats']['current_students']}
        }
        session_data['live_stats']['recent_activities'].append(activity)

        # Keep only last 10 activities
        if len(session_data['live_stats']['recent_activities']) > 10:
            session_data['live_stats']['recent_activities'] = session_data['live_stats']['recent_activities'][-10:]

        # Save updated data to persistent storage
        try:
            await self.storage_service.save_session(session_id, session_data)
            await self.storage_service.save_session_students(session_id, self.session_students[session_id])
            print(f"💾 Updated session {session_id} with new student {student_id}")
        except Exception as e:
            print(f"❌ Failed to save student join for session {session_id}: {e}")

        return {
            'student_id': student_id,
            'session_config': SessionConfig(**session_data['config']),
            'session_status': session_data['status']
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
        """Update student progress and session stats"""
        await self._ensure_data_loaded()
        if session_id not in self.session_students:
            return False

        student_data = self.session_students[session_id].get(student_id)
        if not student_data:
            return False

        now = self.get_korea_time()
        student_data['last_active'] = now.isoformat()  # Convert to ISO string with timezone
        student_data['progress']['current_score'] = understanding_score
        student_data['progress']['dimensions'] = dimensions
        student_data['progress']['conversation_turns'] += 1

        if last_message:
            student_data['messages'].append({
                'content': last_message,
                'timestamp': now.isoformat(),  # Convert to ISO string with timezone
                'type': 'user'
            })

        if is_completed and not student_data['progress']['is_completed']:
            student_data['progress']['is_completed'] = True
            student_data['progress']['completed_at'] = now.isoformat()  # Convert to ISO string with timezone

            # Log completion activity
            session_data = self.active_sessions.get(session_id)
            if session_data:
                activity = {
                    'type': 'student_completed',
                    'student_id': student_id,
                    'student_name': student_data.get('name', '익명'),
                    'timestamp': now.isoformat(),  # Convert to ISO string with timezone
                    'data': {'final_score': understanding_score}
                }
                session_data['live_stats']['recent_activities'].append(activity)

        # Update session live stats
        await self._update_session_live_stats(session_id)

        # Save updated student progress to persistent storage
        try:
            await self.storage_service.save_session_students(session_id, self.session_students[session_id])
            await self.storage_service.save_session(session_id, self.active_sessions[session_id])
        except Exception as e:
            print(f"❌ Failed to save student progress for session {session_id}: {e}")

        return True

    async def end_session(self, session_id: str, teacher_fingerprint: str) -> Optional[Dict[str, Any]]:
        """Delete a session (simplified from end)"""
        return await self.delete_session(session_id, teacher_fingerprint)

    async def delete_session(self, session_id: str, teacher_fingerprint: str) -> bool:
        """Delete a session"""
        await self._ensure_data_loaded()
        session_data = self.active_sessions.get(session_id)
        if not session_data or session_data['teacher_fingerprint'] != teacher_fingerprint:
            return False

        # Remove from memory
        self.active_sessions.pop(session_id, None)
        self.session_students.pop(session_id, None)

        # Remove from persistent storage
        try:
            await self.storage_service.delete_session(session_id)
            print(f"💾 Deleted session {session_id} from persistent storage")
        except Exception as e:
            print(f"❌ Failed to delete session {session_id} from storage: {e}")

        return True

    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        await self._ensure_data_loaded()
        now = self.get_korea_time()
        expired_sessions = []

        for session_id, session_data in self.active_sessions.items():
            expires_at_str = session_data.get('expires_at')
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if expires_at.tzinfo is None:
                        expires_at = self.kst.localize(expires_at)
                    elif expires_at.tzinfo != self.kst:
                        expires_at = expires_at.astimezone(self.kst)

                    if expires_at < now:
                        expired_sessions.append(session_id)
                except Exception as e:
                    print(f"❌ Error parsing expires_at for session {session_id}: {e}")

        # Remove expired sessions immediately
        for session_id in expired_sessions:
            print(f"🗑️ Cleaning up expired session: {session_id}")
            self.active_sessions.pop(session_id, None)
            self.session_students.pop(session_id, None)

            # Remove from persistent storage
            try:
                await self.storage_service.delete_session(session_id)
                print(f"💾 Removed expired session {session_id} from storage")
            except Exception as e:
                print(f"❌ Failed to remove expired session {session_id} from storage: {e}")

    def _calculate_student_progress(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate student progress for display"""
        progress = student_data['progress']
        now = self.get_korea_time()

        # Parse joined_at from ISO string
        if isinstance(student_data['joined_at'], str):
            from datetime import datetime
            # Parse Korean timezone ISO string back to datetime
            joined_at = datetime.fromisoformat(student_data['joined_at'])
            # Make sure it's in Korean timezone
            if joined_at.tzinfo is None:
                joined_at = self.kst.localize(joined_at)
            elif joined_at.tzinfo != self.kst:
                joined_at = joined_at.astimezone(self.kst)
        else:
            joined_at = student_data['joined_at']

        # Parse last_active from ISO string
        if isinstance(student_data['last_active'], str):
            from datetime import datetime
            last_active = datetime.fromisoformat(student_data['last_active'])
            if last_active.tzinfo is None:
                last_active = self.kst.localize(last_active)
            elif last_active.tzinfo != self.kst:
                last_active = last_active.astimezone(self.kst)
        else:
            last_active = student_data['last_active']

        time_spent = int((now - joined_at).total_seconds() / 60)  # minutes
        minutes_since_last_activity = int((now - last_active).total_seconds() / 60)  # minutes

        # Calculate overall progress percentage
        avg_dimension = sum(progress['dimensions'].values()) / len(progress['dimensions'])
        progress_percentage = min(100, int(avg_dimension))

        # Count actual user messages (not system messages)
        user_messages = [msg for msg in student_data['messages'] if msg.get('type') == 'user']
        message_count = len(user_messages)

        return {
            'student_id': student_data['id'],
            'student_name': student_data.get('name', '익명'),
            'latest_score': progress['current_score'],  # 최근 점수
            'message_count': message_count,  # 학생이 보낸 메시지 수
            'joined_at': joined_at,  # 최초 접속 시간
            'last_activity': last_active,  # 최근 활동 시간
            'minutes_since_last_activity': minutes_since_last_activity,  # 마지막 활동으로부터 몇 분 전
            'time_spent': time_spent,  # 총 참여 시간
            'progress_percentage': progress_percentage,
            'conversation_turns': progress['conversation_turns'],
            'current_dimensions': progress['dimensions'],
            'last_message': student_data['messages'][-1]['content'] if student_data['messages'] else None,
            'is_completed': progress['is_completed']
        }

    async def _update_session_live_stats(self, session_id: str):
        """Update session live statistics"""
        session_data = self.active_sessions.get(session_id)
        students = self.session_students.get(session_id, {})

        if not session_data or not students:
            return

        total_students = len(students)
        completed_students = sum(1 for s in students.values() if s['progress']['is_completed'])

        # Calculate averages
        if total_students > 0:
            total_score = sum(s['progress']['current_score'] for s in students.values())
            session_data['live_stats']['average_score'] = total_score / total_students
            session_data['live_stats']['completion_rate'] = (completed_students / total_students) * 100

            # Calculate dimension averages
            for dim in ['depth', 'breadth', 'application', 'metacognition', 'engagement']:
                total_dim = sum(s['progress']['dimensions'][dim] for s in students.values())
                session_data['live_stats']['dimension_averages'][dim] = total_dim / total_students

        session_data['live_stats']['current_students'] = total_students


# Singleton instance
_session_service = SessionService()

def get_session_service() -> SessionService:
    return _session_service