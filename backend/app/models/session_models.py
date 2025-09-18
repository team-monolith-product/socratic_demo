from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class SessionConfig(BaseModel):
    title: str
    topic: str
    description: Optional[str] = None
    difficulty: str = "normal"  # easy, normal, hard
    show_score: bool = True
    time_limit: int = 60  # minutes
    max_students: int = 50

class SessionCreateRequest(BaseModel):
    config: SessionConfig
    teacher_fingerprint: str

class QRCodeInfo(BaseModel):
    url: str
    image_data: str  # base64 encoded PNG
    download_url: str

class SessionInfo(BaseModel):
    id: str
    config: SessionConfig
    status: str  # active (single state)
    created_at: datetime
    expires_at: datetime

class SessionCreateResponse(BaseModel):
    success: bool
    session: SessionInfo
    qr_code: QRCodeInfo

class StudentProgress(BaseModel):
    student_id: str
    student_name: str
    progress_percentage: int
    conversation_turns: int
    time_spent: int  # minutes
    current_dimensions: Dict[str, int]
    last_activity: datetime
    last_message: Optional[str] = None
    is_completed: bool = False

class LiveStats(BaseModel):
    current_students: int
    total_joined: int
    average_score: float
    completion_rate: float
    dimension_averages: Dict[str, float]
    recent_activities: List[Dict[str, Any]]

class SessionActivity(BaseModel):
    type: str  # join, complete, message, milestone
    student_id: Optional[str] = None
    timestamp: datetime
    data: Dict[str, Any]

class SessionDetailsResponse(BaseModel):
    session: SessionInfo
    live_stats: LiveStats
    students: List[StudentProgress]

class SessionJoinRequest(BaseModel):
    student_name: str

class SessionJoinResponse(BaseModel):
    success: bool
    student_id: str
    session_config: SessionConfig
    initial_message: str
    understanding_score: int = 0

class TeacherSessionsResponse(BaseModel):
    sessions: List[Dict[str, Any]]
    summary: Dict[str, Any]