from pydantic import BaseModel
from typing import Optional, List
from fastapi import UploadFile

class PdfAnalysisRequest(BaseModel):
    """PDF 분석 요청 모델"""
    difficulty: str = "normal"  # easy, normal, hard

class PdfAnalysisResult(BaseModel):
    """PDF 분석 결과 모델"""
    original_text: str
    summary: str  # 학습 주제 설명
    key_concepts: List[str]
    main_keyword: str  # 가장 중요한 대표 키워드 하나
    learning_objectives: List[str]
    estimated_duration: int  # 분 단위
    success: bool
    error_message: Optional[str] = None

class TopicCombineRequest(BaseModel):
    """주제 통합 요청 모델"""
    pdf_content: Optional[str] = None
    manual_content: Optional[str] = None
    difficulty: str = "normal"

class TopicCombineResult(BaseModel):
    """주제 통합 결과 모델"""
    combined_topic: str
    source_type: str  # "pdf", "manual", "hybrid"
    success: bool
    error_message: Optional[str] = None