import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from app.models.session_models import (
    SessionConfig, SessionInfo, StudentProgress, LiveStats,
    SessionActivity, QRCodeInfo
)

class SessionService:
    def __init__(self):
        # In-memory storage for active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_students: Dict[str, Dict[str, Any]] = {}  # session_id -> {student_id -> student_data}

    def generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = str(int(datetime.now().timestamp()))[-8:]  # Last 8 digits
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
        session_id = self.generate_session_id()
        now = datetime.now()
        expires_at = now + timedelta(hours=2)  # Sessions expire after 2 hours

        session_data = {
            'id': session_id,
            'teacher_fingerprint': teacher_fingerprint,
            'config': config.dict(),
            'status': 'waiting',  # waiting, active, completed, expired
            'created_at': now,
            'expires_at': expires_at,
            'last_activity': now,
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

        # Generate QR code URL
        session_url = f"{base_url}/s/{session_id}"

        return {
            'session_id': session_id,
            'session_data': session_data,
            'session_url': session_url
        }

    async def get_teacher_sessions(self, teacher_fingerprint: str) -> List[Dict[str, Any]]:
        """Get all sessions for a teacher"""
        teacher_sessions = []
        for session_id, session_data in self.active_sessions.items():
            if session_data['teacher_fingerprint'] == teacher_fingerprint:
                # Add calculated fields
                session_copy = session_data.copy()
                session_copy['students_count'] = len(session_data['students'])
                teacher_sessions.append(session_copy)

        # Sort by created_at desc
        teacher_sessions.sort(key=lambda x: x['created_at'], reverse=True)
        return teacher_sessions

    async def get_session_details(self, session_id: str, teacher_fingerprint: str) -> Optional[Dict[str, Any]]:
        """Get detailed session information for monitoring"""
        session_data = self.active_sessions.get(session_id)
        if not session_data or session_data['teacher_fingerprint'] != teacher_fingerprint:
            return None

        # Get student progress details
        students = []
        for student_id, student_data in self.session_students.get(session_id, {}).items():
            progress = self._calculate_student_progress(student_data)
            students.append(progress)

        return {
            'session': session_data,
            'students': students
        }

    async def join_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Student joins a session"""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return None

        if session_data['status'] == 'expired':
            return None

        # Generate student ID
        student_id = str(uuid.uuid4())
        now = datetime.now()

        # Create student data
        student_data = {
            'id': student_id,
            'session_id': session_id,
            'joined_at': now,
            'last_active': now,
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

        # Change status to active if first student
        if session_data['status'] == 'waiting':
            session_data['status'] = 'active'

        # Log activity
        activity = {
            'type': 'student_joined',
            'student_id': student_id,
            'timestamp': now,
            'data': {'students_count': session_data['live_stats']['current_students']}
        }
        session_data['live_stats']['recent_activities'].append(activity)

        # Keep only last 10 activities
        if len(session_data['live_stats']['recent_activities']) > 10:
            session_data['live_stats']['recent_activities'] = session_data['live_stats']['recent_activities'][-10:]

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
        if session_id not in self.session_students:
            return False

        student_data = self.session_students[session_id].get(student_id)
        if not student_data:
            return False

        now = datetime.now()
        student_data['last_active'] = now
        student_data['progress']['current_score'] = understanding_score
        student_data['progress']['dimensions'] = dimensions
        student_data['progress']['conversation_turns'] += 1

        if last_message:
            student_data['messages'].append({
                'content': last_message,
                'timestamp': now,
                'type': 'user'
            })

        if is_completed and not student_data['progress']['is_completed']:
            student_data['progress']['is_completed'] = True
            student_data['progress']['completed_at'] = now

            # Log completion activity
            session_data = self.active_sessions.get(session_id)
            if session_data:
                activity = {
                    'type': 'student_completed',
                    'student_id': student_id,
                    'timestamp': now,
                    'data': {'final_score': understanding_score}
                }
                session_data['live_stats']['recent_activities'].append(activity)

        # Update session live stats
        await self._update_session_live_stats(session_id)
        return True

    async def end_session(self, session_id: str, teacher_fingerprint: str) -> Optional[Dict[str, Any]]:
        """End a session"""
        session_data = self.active_sessions.get(session_id)
        if not session_data or session_data['teacher_fingerprint'] != teacher_fingerprint:
            return None

        session_data['status'] = 'completed'
        session_data['ended_at'] = datetime.now()

        # Calculate final stats
        final_stats = await self._calculate_final_stats(session_id)

        return final_stats

    async def delete_session(self, session_id: str, teacher_fingerprint: str) -> bool:
        """Delete a session"""
        session_data = self.active_sessions.get(session_id)
        if not session_data or session_data['teacher_fingerprint'] != teacher_fingerprint:
            return False

        # Remove from memory
        self.active_sessions.pop(session_id, None)
        self.session_students.pop(session_id, None)

        return True

    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_sessions = []

        for session_id, session_data in self.active_sessions.items():
            if session_data['expires_at'] < now:
                session_data['status'] = 'expired'
                expired_sessions.append(session_id)

        # Remove expired sessions after 1 hour
        for session_id in expired_sessions:
            session_data = self.active_sessions[session_id]
            if session_data['expires_at'] < (now - timedelta(hours=1)):
                self.active_sessions.pop(session_id, None)
                self.session_students.pop(session_id, None)

    def _calculate_student_progress(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate student progress for display"""
        progress = student_data['progress']
        now = datetime.now()
        joined_at = student_data['joined_at']
        time_spent = int((now - joined_at).total_seconds() / 60)  # minutes

        # Calculate overall progress percentage
        avg_dimension = sum(progress['dimensions'].values()) / len(progress['dimensions'])
        progress_percentage = min(100, int(avg_dimension))

        return {
            'student_id': student_data['id'],
            'progress_percentage': progress_percentage,
            'conversation_turns': progress['conversation_turns'],
            'time_spent': time_spent,
            'current_dimensions': progress['dimensions'],
            'last_activity': student_data['last_active'],
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

    async def _calculate_final_stats(self, session_id: str) -> Dict[str, Any]:
        """Calculate final session statistics"""
        session_data = self.active_sessions.get(session_id)
        students = self.session_students.get(session_id, {})

        if not session_data:
            return {}

        total_students = len(students)
        completed_students = sum(1 for s in students.values() if s['progress']['is_completed'])

        final_stats = {
            'total_students': total_students,
            'completed_students': completed_students,
            'completion_rate': (completed_students / total_students * 100) if total_students > 0 else 0,
            'average_score': session_data['live_stats']['average_score'],
            'dimension_averages': session_data['live_stats']['dimension_averages'].copy()
        }

        return final_stats

# Singleton instance
_session_service = SessionService()

def get_session_service() -> SessionService:
    return _session_service