from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TopicInputRequest(BaseModel):
    topic_content: str
    content_type: str = "text"  # "text", "pdf", "url" (향후 확장)

class SocraticChatRequest(BaseModel):
    topic: str
    messages: List[Dict[str, str]]
    understanding_level: int = 0
    difficulty: str = "normal"  # "easy", "normal", "hard"

class SocraticChatResponse(BaseModel):
    socratic_response: str
    understanding_score: int
    is_completed: bool = False
    # 5차원 소크라테스식 평가 결과
    dimensions: Optional[Dict[str, int]] = None
    insights: Optional[Dict[str, str]] = None
    growth_indicators: Optional[List[str]] = None
    next_focus: Optional[str] = None

class InitialMessageRequest(BaseModel):
    topic: str
    difficulty: str = "normal"

class InitialMessageResponse(BaseModel):
    initial_message: str
    understanding_score: int = 0