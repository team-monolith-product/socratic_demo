from pydantic import BaseModel
from typing import Optional, List
from fastapi import UploadFile

class PdfAnalysisRequest(BaseModel):
    """PDF 분석 요청 모델"""
    difficulty: str = "normal"  # easy, normal, hard

class PdfAnalysisResult(BaseModel):
    """PDF 분석 결과 모델 (통합 기능용으로 단순화)"""
    original_text: str
    compressed_content: str  # 압축된 PDF 본문 (핵심 기능)
    one_sentence_topic: str  # 한 문장 학습 주제 (UI 노출용, 핵심 기능)
    success: bool
    error_message: Optional[str] = None

    # 레거시 필드들 (하위 호환성을 위해 기본값 제공)
    summary: str = ""
    key_concepts: List[str] = []
    main_keyword: str = ""
    learning_objectives: List[str] = []
    estimated_duration: int = 30

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