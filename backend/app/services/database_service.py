"""Database service using SQLAlchemy to replace file-based storage."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import pytz

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import AsyncSessionLocal
from app.models.database_models import Teacher, Session, Student, Message, Score


class DatabaseService:
    """Database service for persistent storage using SQLAlchemy."""

    def __init__(self):
        self.kst = pytz.timezone('Asia/Seoul')

    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        return AsyncSessionLocal()

    async def get_or_create_teacher(self, fingerprint: str) -> str:
        """Get or create teacher by fingerprint and return teacher_id."""
        async with await self._get_session() as session:
            # Try to find existing teacher
            stmt = select(Teacher).where(Teacher.fingerprint == fingerprint)
            result = await session.execute(stmt)
            teacher = result.scalar_one_or_none()

            if teacher:
                # Update last_seen
                teacher.last_seen = datetime.now(self.kst)
                await session.commit()
                return teacher.id
            else:
                # Create new teacher
                teacher = Teacher(fingerprint=fingerprint)
                session.add(teacher)
                await session.commit()
                return teacher.id

    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Save a session to database."""
        try:
            async with await self._get_session() as db_session:
                teacher_id = await self.get_or_create_teacher(session_data['teacher_fingerprint'])

                # Check if session exists
                stmt = select(Session).where(Session.id == session_id)
                result = await db_session.execute(stmt)
                existing_session = result.scalar_one_or_none()

                if existing_session:
                    # Update existing session
                    existing_session.title = session_data['config'].get('title')
                    existing_session.topic = session_data['config']['topic']
                    existing_session.description = session_data['config'].get('description')
                    existing_session.difficulty = session_data['config'].get('difficulty', 'normal')
                    existing_session.show_score = session_data['config'].get('show_score', True)
                    existing_session.time_limit = session_data['config'].get('time_limit')
                    existing_session.max_students = session_data['config'].get('max_students')
                    existing_session.status = session_data.get('status', 'active')
                    existing_session.last_activity = self._parse_datetime(session_data.get('last_activity'))
                    existing_session.ended_at = self._parse_datetime(session_data.get('ended_at'))

                    # Update enhanced topic tracking fields
                    self._update_topic_fields(existing_session, session_data['config'])
                else:
                    # Create new session
                    new_session = Session(
                        id=session_id,
                        teacher_id=teacher_id,
                        title=session_data['config'].get('title'),
                        topic=session_data['config']['topic'],
                        description=session_data['config'].get('description'),
                        difficulty=session_data['config'].get('difficulty', 'normal'),
                        show_score=session_data['config'].get('show_score', True),
                        time_limit=session_data['config'].get('time_limit'),
                        max_students=session_data['config'].get('max_students'),
                        status=session_data.get('status', 'active'),
                        created_at=self._parse_datetime(session_data.get('created_at')),
                        expires_at=self._parse_datetime(session_data['expires_at']),
                        last_activity=self._parse_datetime(session_data.get('last_activity')),
                        ended_at=self._parse_datetime(session_data.get('ended_at'))
                    )

                    # Set enhanced topic tracking fields for new session
                    self._update_topic_fields(new_session, session_data['config'])
                    db_session.add(new_session)

                await db_session.commit()
                return True
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            return False

    async def load_sessions(self) -> Dict[str, Any]:
        """Load all active (non-deleted) sessions from database."""
        try:
            async with await self._get_session() as session:
                stmt = select(Session).options(selectinload(Session.teacher)).where(Session.deleted_at.is_(None))
                result = await session.execute(stmt)
                db_sessions = result.scalars().all()

                sessions_dict = {}
                for db_session in db_sessions:
                    sessions_dict[db_session.id] = {
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
                        'last_activity': db_session.last_activity.isoformat(),
                        'ended_at': db_session.ended_at.isoformat() if db_session.ended_at else None,
                        'students': {},  # Will be populated separately
                        'live_stats': await self._calculate_live_stats(db_session.id),
                    }

                return sessions_dict
        except Exception as e:
            print(f"Error loading sessions: {e}")
            return {}

    async def save_session_students(self, session_id: str, session_students: Dict[str, Any]) -> bool:
        """Save students for a specific session."""
        try:
            async with await self._get_session() as db_session:
                for student_id, student_data in session_students.items():
                    # Check if student exists
                    stmt = select(Student).where(Student.id == student_id)
                    result = await db_session.execute(stmt)
                    existing_student = result.scalar_one_or_none()

                    if existing_student:
                        # Update existing student
                        existing_student.name = student_data.get('name', '익명')
                        existing_student.token = student_data.get('token')  # Update token
                        existing_student.last_active = self._parse_datetime(student_data.get('last_active'))
                        existing_student.conversation_turns = student_data['progress'].get('conversation_turns', 0)
                        existing_student.current_score = student_data['progress'].get('current_score', 0)

                        # Update dimension scores
                        dimensions = student_data['progress'].get('dimensions', {})
                        existing_student.depth_score = dimensions.get('depth', 0)
                        existing_student.breadth_score = dimensions.get('breadth', 0)
                        existing_student.application_score = dimensions.get('application', 0)
                        existing_student.metacognition_score = dimensions.get('metacognition', 0)
                        existing_student.engagement_score = dimensions.get('engagement', 0)

                        existing_student.is_completed = student_data['progress'].get('is_completed', False)
                        existing_student.completed_at = self._parse_datetime(student_data['progress'].get('completed_at'))
                    else:
                        # Create new student
                        new_student = Student(
                            id=student_id,
                            session_id=session_id,
                            name=student_data.get('name', '익명'),
                            token=student_data.get('token'),  # Include token
                            joined_at=self._parse_datetime(student_data.get('joined_at')),
                            last_active=self._parse_datetime(student_data.get('last_active')),
                            conversation_turns=student_data['progress'].get('conversation_turns', 0),
                            current_score=student_data['progress'].get('current_score', 0),
                            depth_score=student_data['progress'].get('dimensions', {}).get('depth', 0),
                            breadth_score=student_data['progress'].get('dimensions', {}).get('breadth', 0),
                            application_score=student_data['progress'].get('dimensions', {}).get('application', 0),
                            metacognition_score=student_data['progress'].get('dimensions', {}).get('metacognition', 0),
                            engagement_score=student_data['progress'].get('dimensions', {}).get('engagement', 0),
                            is_completed=student_data['progress'].get('is_completed', False),
                            completed_at=self._parse_datetime(student_data['progress'].get('completed_at'))
                        )
                        db_session.add(new_student)

                    # Save messages
                    await self._save_student_messages(db_session, student_id, session_id, student_data.get('messages', []))

                await db_session.commit()
                return True
        except Exception as e:
            print(f"Error saving students for session {session_id}: {e}")
            return False

    async def load_students(self) -> Dict[str, Any]:
        """Load all student data from database."""
        try:
            async with await self._get_session() as session:
                stmt = select(Student).options(selectinload(Student.messages))
                result = await session.execute(stmt)
                db_students = result.scalars().all()

                students_dict = {}
                for student in db_students:
                    session_id = student.session_id
                    if session_id not in students_dict:
                        students_dict[session_id] = {}

                    students_dict[session_id][student.id] = {
                        'id': student.id,
                        'name': student.name,
                        'session_id': student.session_id,
                        'token': student.token,  # Include token
                        'joined_at': student.joined_at.isoformat(),
                        'last_active': student.last_active.isoformat(),
                        'progress': {
                            'conversation_turns': student.conversation_turns,
                            'current_score': student.current_score,
                            'dimensions': {
                                'depth': student.depth_score,
                                'breadth': student.breadth_score,
                                'application': student.application_score,
                                'metacognition': student.metacognition_score,
                                'engagement': student.engagement_score
                            },
                            'is_completed': student.is_completed,
                            'completed_at': student.completed_at.isoformat() if student.completed_at else None
                        },
                        'messages': [
                            {
                                'content': msg.content,
                                'timestamp': msg.timestamp.isoformat(),
                                'type': msg.message_type
                            }
                            for msg in sorted(student.messages, key=lambda x: x.timestamp, reverse=True)
                        ]
                    }

                return students_dict
        except Exception as e:
            print(f"Error loading students: {e}")
            return {}

    async def delete_session(self, session_id: str) -> bool:
        """Soft delete a session (mark as deleted but keep data)."""
        try:
            async with await self._get_session() as session:
                stmt = update(Session).where(Session.id == session_id).values(
                    deleted_at=datetime.now(self.kst)
                )
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            print(f"Error soft deleting session {session_id}: {e}")
            return False

    async def hard_delete_session(self, session_id: str) -> bool:
        """Hard delete a session from database (permanent removal)."""
        try:
            async with await self._get_session() as session:
                stmt = delete(Session).where(Session.id == session_id)
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            print(f"Error hard deleting session {session_id}: {e}")
            return False

    async def _save_student_messages(self, db_session: AsyncSession, student_id: str, session_id: str, messages: List[Dict]):
        """Save student messages to database without deleting existing ones."""
        # DO NOT DELETE existing messages - they should persist
        # Only add new messages that don't already exist

        # Add new messages (skip if content already exists to avoid duplicates)
        for msg in messages:
            content = msg.get('content', '')
            if content:  # Only save non-empty messages
                # Check if message already exists
                existing_stmt = select(Message).where(
                    Message.student_id == student_id,
                    Message.content == content,
                    Message.message_type == msg.get('type', 'user')
                )
                existing = await db_session.execute(existing_stmt)
                if existing.scalar_one_or_none() is None:
                    # Message doesn't exist, create new one
                    new_message = Message(
                        student_id=student_id,
                        session_id=session_id,
                        content=content,
                        message_type=msg.get('type', 'user'),
                        timestamp=self._parse_datetime(msg.get('timestamp'))
                    )
                    db_session.add(new_message)

    async def _calculate_live_stats(self, session_id: str) -> Dict[str, Any]:
        """Calculate live statistics for a session."""
        try:
            async with await self._get_session() as session:
                # Count students
                stmt = select(func.count(Student.id)).where(Student.session_id == session_id)
                result = await session.execute(stmt)
                total_joined = result.scalar() or 0

                # Count completed students
                stmt = select(func.count(Student.id)).where(
                    and_(Student.session_id == session_id, Student.is_completed == True)
                )
                result = await session.execute(stmt)
                completed_count = result.scalar() or 0

                # Calculate averages
                stmt = select(
                    func.avg(Student.current_score),
                    func.avg(Student.depth_score),
                    func.avg(Student.breadth_score),
                    func.avg(Student.application_score),
                    func.avg(Student.metacognition_score),
                    func.avg(Student.engagement_score)
                ).where(Student.session_id == session_id)
                result = await session.execute(stmt)
                averages = result.first()

                return {
                    'current_students': total_joined,
                    'total_joined': total_joined,
                    'average_score': float(averages[0] or 0),
                    'completion_rate': (completed_count / max(total_joined, 1)) * 100,
                    'dimension_averages': {
                        'depth': float(averages[1] or 0),
                        'breadth': float(averages[2] or 0),
                        'application': float(averages[3] or 0),
                        'metacognition': float(averages[4] or 0),
                        'engagement': float(averages[5] or 0)
                    },
                    'recent_activities': []
                }
        except Exception as e:
            print(f"Error calculating live stats for session {session_id}: {e}")
            return {
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
            }

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return None
        try:
            if isinstance(dt_str, str):
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt_str
        except Exception:
            return None

    def _format_korea_time(self, dt: datetime) -> str:
        """Format datetime to Korean timezone ISO string."""
        if not dt:
            return None
        try:
            # If datetime is naive (no timezone), assume it's UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)

            # Convert to Korean timezone
            korea_time = dt.astimezone(self.kst)
            return korea_time.isoformat()
        except Exception:
            # Fallback to original isoformat
            return dt.isoformat() if dt else None

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            async with await self._get_session() as session:
                # Count total sessions
                stmt = select(func.count(Session.id))
                result = await session.execute(stmt)
                total_sessions = result.scalar() or 0

                # Count total students
                stmt = select(func.count(Student.id))
                result = await session.execute(stmt)
                total_students = result.scalar() or 0

                return {
                    "total_sessions": total_sessions,
                    "total_students": total_students,
                    "storage_type": "database",
                    "data_directory": "N/A (Database)"
                }
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return {
                "total_sessions": 0,
                "total_students": 0,
                "storage_type": "database",
                "data_directory": "N/A (Database)"
            }

    async def is_database_enabled(self) -> bool:
        """Check if database is enabled."""
        return True  # DatabaseService is always database-enabled

    async def save_message(self, session_id: str, student_id: str, content: str, message_type: str) -> bool:
        """Append message to conversation_data JSON array in messages table."""
        try:
            print(f"🔍 Saving message to conversation_data: session={session_id}, student={student_id}, type={message_type}")

            async with AsyncSessionLocal() as db_session:
                async with db_session.begin():
                    # Check if message record exists for this student
                    message_stmt = select(Message).where(Message.student_id == student_id, Message.session_id == session_id)
                    message_result = await db_session.execute(message_stmt)
                    message_record = message_result.scalar_one_or_none()

                    new_message_entry = {
                        "role": message_type,
                        "content": content
                    }

                    if message_record:
                        # Append to existing conversation_data
                        conversation_data = message_record.conversation_data or []
                        conversation_data.append(new_message_entry)
                        message_record.conversation_data = conversation_data
                        # IMPORTANT: Mark the JSON field as modified for SQLAlchemy to detect changes
                        flag_modified(message_record, "conversation_data")
                        message_record.timestamp = datetime.now(self.kst)
                        print(f"✅ Appended message to existing conversation (total: {len(conversation_data)} messages)")
                    else:
                        # Create new message record with first message
                        new_message_record = Message(
                            student_id=student_id,
                            session_id=session_id,
                            conversation_data=[new_message_entry],
                            timestamp=datetime.now(self.kst)
                        )
                        db_session.add(new_message_record)
                        print(f"✅ Created new message record for student")

                    await db_session.flush()

                print(f"✅ Message saved successfully")
                return True

        except Exception as e:
            print(f"❌ Error saving message: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def get_student_messages(self, session_id: str, student_id: str) -> List[Dict[str, Any]]:
        """Get conversation_data from messages table."""
        try:
            print(f"🔍 Getting conversation_data for session={session_id}, student={student_id}")

            async with AsyncSessionLocal() as db_session:
                # Get message record for this student
                message_stmt = select(Message).where(Message.student_id == student_id, Message.session_id == session_id)
                message_result = await db_session.execute(message_stmt)
                message_record = message_result.scalar_one_or_none()

                if not message_record:
                    print(f"ℹ️ No message record found for student {student_id}")
                    return []

                # Get conversation_data
                conversation_data = message_record.conversation_data or []

                print(f"✅ Loaded {len(conversation_data)} messages from conversation_data")

                # Convert to expected format (role → message_type for compatibility)
                result_list = [
                    {
                        "content": msg.get("content", ""),
                        "message_type": msg.get("role", "user"),  # role → message_type
                        "timestamp": None  # No individual timestamps in JSON storage
                    }
                    for msg in conversation_data
                ]

                return result_list

        except Exception as e:
            print(f"❌ Error getting student messages: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session with student info, ordered by timestamp (newest first)."""
        try:
            async with await self._get_session() as session:
                stmt = select(Message, Student.name).join(
                    Student, Message.student_id == Student.id
                ).where(
                    Message.session_id == session_id
                ).order_by(Message.timestamp.desc())

                result = await session.execute(stmt)
                message_student_pairs = result.all()

                return [
                    {
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "timestamp": self._format_korea_time(msg.timestamp) if msg.timestamp else None,
                        "student_id": msg.student_id,
                        "student_name": student_name
                    }
                    for msg, student_name in message_student_pairs
                ]
        except Exception as e:
            print(f"Error getting session messages: {e}")
            return []

    async def save_score(
        self,
        message_id: str,
        student_id: str,
        session_id: str,
        overall_score: int,
        dimensions: Dict[str, int],
        evaluation_data: Optional[Dict[str, Any]] = None,
        is_completed: bool = False
    ) -> bool:
        """Save a score record for a student response."""
        try:
            async with await self._get_session() as session:
                new_score = Score(
                    message_id=message_id,
                    student_id=student_id,
                    session_id=session_id,
                    overall_score=overall_score,
                    depth_score=dimensions.get('depth', 0),
                    breadth_score=dimensions.get('breadth', 0),
                    application_score=dimensions.get('application', 0),
                    metacognition_score=dimensions.get('metacognition', 0),
                    engagement_score=dimensions.get('engagement', 0),
                    evaluation_data=evaluation_data,
                    is_completed=is_completed,
                    created_at=datetime.now(self.kst)
                )
                session.add(new_score)
                await session.commit()
                return True
        except Exception as e:
            print(f"Error saving score: {e}")
            return False

    async def get_student_scores(self, session_id: str, student_id: str) -> List[Dict[str, Any]]:
        """Get all score records for a specific student in a session."""
        try:
            async with await self._get_session() as session:
                stmt = select(Score).where(
                    and_(Score.session_id == session_id, Score.student_id == student_id)
                ).order_by(Score.created_at.desc())

                result = await session.execute(stmt)
                scores = result.scalars().all()

                return [
                    {
                        "id": score.id,
                        "message_id": score.message_id,
                        "overall_score": score.overall_score,
                        "dimensions": {
                            "depth": score.depth_score,
                            "breadth": score.breadth_score,
                            "application": score.application_score,
                            "metacognition": score.metacognition_score,
                            "engagement": score.engagement_score
                        },
                        "evaluation_data": score.evaluation_data,
                        "is_completed": score.is_completed,
                        "created_at": self._format_korea_time(score.created_at) if score.created_at else None
                    }
                    for score in scores
                ]
        except Exception as e:
            print(f"Error getting student scores: {e}")
            return []

    async def get_session_scores(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all score records for a session."""
        try:
            async with await self._get_session() as session:
                stmt = select(Score, Student.name).join(
                    Student, Score.student_id == Student.id
                ).where(
                    Score.session_id == session_id
                ).order_by(Score.created_at.desc())

                result = await session.execute(stmt)
                score_student_pairs = result.all()

                return [
                    {
                        "id": score.id,
                        "message_id": score.message_id,
                        "student_id": score.student_id,
                        "student_name": student_name,
                        "overall_score": score.overall_score,
                        "dimensions": {
                            "depth": score.depth_score,
                            "breadth": score.breadth_score,
                            "application": score.application_score,
                            "metacognition": score.metacognition_score,
                            "engagement": score.engagement_score
                        },
                        "evaluation_data": score.evaluation_data,
                        "is_completed": score.is_completed,
                        "created_at": self._format_korea_time(score.created_at) if score.created_at else None
                    }
                    for score, student_name in score_student_pairs
                ]
        except Exception as e:
            print(f"Error getting session scores: {e}")
            return []

    async def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        try:
            async with await self._get_session() as session:
                stmt = select(Session).options(selectinload(Session.teacher)).where(
                    and_(Session.id == session_id, Session.deleted_at.is_(None))
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error getting session {session_id}: {e}")
            return None

    async def get_student_by_token(self, session_id: str, token: str) -> Optional[Student]:
        """Get a student by token in a specific session."""
        try:
            async with await self._get_session() as session:
                stmt = select(Student).where(
                    and_(Student.session_id == session_id, Student.token == token)
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error getting student by token: {e}")
            return None

    async def get_student_by_name(self, session_id: str, name: str) -> Optional[Student]:
        """Get a student by name in a specific session."""
        try:
            async with await self._get_session() as session:
                stmt = select(Student).where(
                    and_(Student.session_id == session_id, func.lower(Student.name) == name.lower())
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error getting student by name: {e}")
            return None

    async def get_student_by_id(self, student_id: str) -> Optional[Student]:
        """Get a student by ID."""
        try:
            async with await self._get_session() as session:
                stmt = select(Student).where(Student.id == student_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error getting student by ID: {e}")
            return None

    async def get_students_by_session(self, session_id: str) -> List[Student]:
        """Get all students in a session."""
        try:
            async with await self._get_session() as session:
                stmt = select(Student).where(Student.session_id == session_id).order_by(Student.joined_at)
                result = await session.execute(stmt)
                return result.scalars().all()
        except Exception as e:
            print(f"Error getting students for session {session_id}: {e}")
            return []

    async def get_message_count(self, student_id: str, message_type: str = 'user') -> int:
        """Get count of messages for a student by type."""
        try:
            async with await self._get_session() as session:
                stmt = select(func.count(Message.id)).where(
                    and_(Message.student_id == student_id, Message.message_type == message_type)
                )
                result = await session.execute(stmt)
                return result.scalar() or 0
        except Exception as e:
            print(f"Error getting message count: {e}")
            return 0

    async def update_student_progress(
        self,
        student_id: str,
        understanding_score: int,
        dimensions: Dict[str, int],
        is_completed: bool = False
    ) -> bool:
        """Update student progress in database."""
        try:
            async with await self._get_session() as session:
                stmt = select(Student).where(Student.id == student_id)
                result = await session.execute(stmt)
                student = result.scalar_one_or_none()

                if not student:
                    return False

                # Update student fields
                student.last_active = datetime.now(self.kst)
                student.current_score = understanding_score
                student.conversation_turns += 1
                student.depth_score = dimensions.get('depth', 0)
                student.breadth_score = dimensions.get('breadth', 0)
                student.application_score = dimensions.get('application', 0)
                student.metacognition_score = dimensions.get('metacognition', 0)
                student.engagement_score = dimensions.get('engagement', 0)

                if is_completed and not student.is_completed:
                    student.is_completed = True
                    student.completed_at = datetime.now(self.kst)

                await session.commit()
                return True
        except Exception as e:
            print(f"Error updating student progress: {e}")
            return False

    async def create_student(
        self,
        student_id: str,
        session_id: str,
        name: str,
        token: str
    ) -> Optional[Student]:
        """Create a new student."""
        try:
            async with await self._get_session() as session:
                new_student = Student(
                    id=student_id,
                    session_id=session_id,
                    name=name,
                    token=token,
                    joined_at=datetime.now(self.kst),
                    last_active=datetime.now(self.kst),
                    conversation_turns=0,
                    current_score=0,
                    depth_score=0,
                    breadth_score=0,
                    application_score=0,
                    metacognition_score=0,
                    engagement_score=0,
                    is_completed=False
                )
                session.add(new_student)
                await session.commit()
                await session.refresh(new_student)
                return new_student
        except Exception as e:
            print(f"Error creating student: {e}")
            return None

    async def update_student_last_active(self, student_id: str) -> bool:
        """Update student's last active timestamp."""
        try:
            async with await self._get_session() as session:
                stmt = update(Student).where(Student.id == student_id).values(
                    last_active=datetime.now(self.kst)
                )
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            print(f"Error updating student last active: {e}")
            return False

    async def get_sessions_by_teacher(self, teacher_fingerprint: str) -> List[Session]:
        """Get all non-deleted sessions for a teacher."""
        try:
            async with await self._get_session() as session:
                # First get teacher
                teacher_stmt = select(Teacher).where(Teacher.fingerprint == teacher_fingerprint)
                teacher_result = await session.execute(teacher_stmt)
                teacher = teacher_result.scalar_one_or_none()

                if not teacher:
                    return []

                # Get sessions
                stmt = select(Session).where(
                    and_(Session.teacher_id == teacher.id, Session.deleted_at.is_(None))
                ).order_by(Session.created_at.desc())
                result = await session.execute(stmt)
                return result.scalars().all()
        except Exception as e:
            print(f"Error getting sessions for teacher: {e}")
            return []





    def _update_topic_fields(self, session, config: Dict[str, Any]):
        """Update enhanced topic tracking fields from session config."""
        # Determine topic type and source
        source_type = config.get('source_type', 'manual')

        # Map source types to our enhanced classification
        if source_type == 'manual':
            session.topic_type = 'manual'
            session.topic_source = 'manual'
            session.manual_topic_content = config.get('manual_content') or config.get('topic')
            session.final_topic_content = config.get('combined_topic') or config.get('topic')
        elif source_type == 'pdf':
            # Determine which PDF variant based on what's available
            if config.get('pdf_content'):
                # Check if it's the compressed content (longer) or others
                pdf_content = config.get('pdf_content', '')
                if len(pdf_content) > 500:  # Likely the compressed content (요약 줄글)
                    session.topic_type = 'pdf_summary'
                    session.pdf_summary_topic = pdf_content
                elif len(pdf_content) < 50:  # Likely noun topic (명사형)
                    session.topic_type = 'pdf_noun'
                    session.pdf_noun_topic = pdf_content
                else:  # Likely sentence topic (한 문장)
                    session.topic_type = 'pdf_sentence'
                    session.pdf_sentence_topic = pdf_content
            else:
                session.topic_type = 'pdf_summary'  # Default fallback

            session.topic_source = 'pdf'
            session.pdf_original_content = config.get('original_text')
            session.final_topic_content = config.get('combined_topic') or config.get('topic')
        elif source_type == 'hybrid':
            session.topic_type = 'hybrid'
            session.topic_source = 'hybrid'
            session.pdf_summary_topic = config.get('pdf_content')
            session.manual_topic_content = config.get('manual_content')
            session.final_topic_content = config.get('combined_topic') or config.get('topic')
        else:
            # Fallback to manual
            session.topic_type = 'manual'
            session.topic_source = 'manual'
            session.manual_topic_content = config.get('topic')
            session.final_topic_content = config.get('topic')

        # Store additional metadata
        session.topic_metadata = {
            'source_type': source_type,
            'key_concepts': config.get('key_concepts', []),
            'learning_objectives': config.get('learning_objectives', []),
            'main_keyword': config.get('main_keyword'),
            'processing_timestamp': datetime.now(self.kst).isoformat()
        }


# Singleton instance
_database_service = DatabaseService()

def get_database_service() -> DatabaseService:
    """Get database service instance."""
    return _database_service