from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class SessionConfig(BaseModel):
    title: str
    topic: str
    description: Optional[str] = None
    difficulty: str = "normal"  # easy, normal, hard
    show_score: bool = True

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
    latest_score: int  # 최근 점수
    message_count: int  # 학생이 보낸 메시지 수
    joined_at: datetime  # 최초 접속 시간
    last_activity: datetime  # 최근 활동 시간
    minutes_since_last_activity: int  # 마지막 활동으로부터 몇 분 전
    time_spent: int  # 총 참여 시간 (분)
    progress_percentage: int
    conversation_turns: int
    current_dimensions: Dict[str, int]
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