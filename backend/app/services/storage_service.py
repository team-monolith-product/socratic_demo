import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import pytz
import asyncio
import aiofiles
from pathlib import Path

class StorageService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.sessions_file = self.data_dir / "sessions.json"
        self.students_file = self.data_dir / "students.json"
        self.kst = pytz.timezone('Asia/Seoul')

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)

        # Initialize empty files if they don't exist
        if not self.sessions_file.exists():
            self.sessions_file.write_text(json.dumps({}))
        if not self.students_file.exists():
            self.students_file.write_text(json.dumps({}))

    async def load_sessions(self) -> Dict[str, Any]:
        """Load all sessions from file"""
        try:
            if self.sessions_file.exists():
                async with aiofiles.open(self.sessions_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    return json.loads(content) if content.strip() else {}
            return {}
        except Exception as e:
            print(f"Error loading sessions: {e}")
            return {}

    async def save_sessions(self, sessions: Dict[str, Any]) -> bool:
        """Save all sessions to file"""
        try:
            # Create a copy with serializable data
            serializable_sessions = {}
            for session_id, session_data in sessions.items():
                serializable_sessions[session_id] = self._make_serializable(session_data)

            async with aiofiles.open(self.sessions_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(serializable_sessions, indent=2, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"Error saving sessions: {e}")
            return False

    async def load_students(self) -> Dict[str, Any]:
        """Load all student data from file"""
        try:
            if self.students_file.exists():
                async with aiofiles.open(self.students_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    return json.loads(content) if content.strip() else {}
            return {}
        except Exception as e:
            print(f"Error loading students: {e}")
            return {}

    async def save_students(self, students: Dict[str, Any]) -> bool:
        """Save all student data to file"""
        try:
            # Create a copy with serializable data
            serializable_students = {}
            for session_id, session_students in students.items():
                serializable_students[session_id] = {}
                for student_id, student_data in session_students.items():
                    serializable_students[session_id][student_id] = self._make_serializable(student_data)

            async with aiofiles.open(self.students_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(serializable_students, indent=2, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"Error saving students: {e}")
            return False

    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Save a single session"""
        sessions = await self.load_sessions()
        sessions[session_id] = self._make_serializable(session_data)
        return await self.save_sessions(sessions)

    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a single session"""
        sessions = await self.load_sessions()
        return sessions.get(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session from storage"""
        sessions = await self.load_sessions()
        if session_id in sessions:
            del sessions[session_id]
            await self.save_sessions(sessions)

            # Also delete student data for this session
            students = await self.load_students()
            if session_id in students:
                del students[session_id]
                await self.save_students(students)

            return True
        return False

    async def save_session_students(self, session_id: str, session_students: Dict[str, Any]) -> bool:
        """Save students for a specific session"""
        students = await self.load_students()
        students[session_id] = {}
        for student_id, student_data in session_students.items():
            students[session_id][student_id] = self._make_serializable(student_data)
        return await self.save_students(students)

    async def load_session_students(self, session_id: str) -> Dict[str, Any]:
        """Load students for a specific session"""
        students = await self.load_students()
        return students.get(session_id, {})

    def _make_serializable(self, data: Any) -> Any:
        """Convert data to JSON serializable format"""
        if isinstance(data, dict):
            return {key: self._make_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, 'dict'):  # Pydantic models
            return self._make_serializable(data.dict())
        else:
            return data

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        sessions = await self.load_sessions()
        students = await self.load_students()

        total_sessions = len(sessions)
        total_students = sum(len(session_students) for session_students in students.values())

        # File sizes
        sessions_size = self.sessions_file.stat().st_size if self.sessions_file.exists() else 0
        students_size = self.students_file.stat().st_size if self.students_file.exists() else 0

        return {
            "total_sessions": total_sessions,
            "total_students": total_students,
            "sessions_file_size": sessions_size,
            "students_file_size": students_size,
            "data_directory": str(self.data_dir.absolute())
        }

    async def is_database_enabled(self) -> bool:
        """Check if database is enabled."""
        return False  # File-based storage is not database-enabled

    async def save_message(self, session_id: str, student_id: str, content: str, message_type: str) -> bool:
        """Save a single message (file-based storage doesn't support individual message tracking)."""
        # For file-based storage, messages are stored as part of student data
        # This is a simplified implementation - in production you might want message-level tracking
        print(f"Message tracking not fully supported in file-based storage mode")
        return True

    async def get_student_messages(self, session_id: str, student_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific student (file-based storage doesn't support this)."""
        # File-based storage doesn't track individual messages
        print(f"Message history not available in file-based storage mode")
        return []

    async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session (file-based storage doesn't support this)."""
        # File-based storage doesn't track individual messages
        print(f"Session message history not available in file-based storage mode")
        return []

# Storage service factory - always returns DatabaseService
def get_storage_service():
    """Get database storage service (PostgreSQL only)."""
    from app.services.database_service import get_database_service
    return get_database_service()