from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from app.models.pdf_models import PdfAnalysisResult, TopicCombineRequest, TopicCombineResult
from app.services.pdf_processing_service import get_pdf_processing_service
from app.services.topic_integration_service import get_topic_integration_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/teacher/analyze-pdf", response_model=PdfAnalysisResult)
async def analyze_pdf(
    pdf_file: UploadFile = File(..., description="분석할 PDF 파일"),
    difficulty: str = Form("normal", description="난이도 (easy/normal/hard)")
):
    """PDF 파일을 분석하여 학습 주제를 생성합니다."""
    try:
        pdf_service = get_pdf_processing_service()

        # PDF에서 텍스트 추출
        extracted_text = await pdf_service.extract_text_from_pdf(pdf_file)
        logger.info(f"PDF 텍스트 추출 완료: {len(extracted_text)}자")

        # 콘텐츠 유효성 검증
        if not await pdf_service.validate_pdf_content(extracted_text):
            raise HTTPException(status_code=400, detail="부적절한 PDF 콘텐츠입니다.")

        # AI 분석 및 요약
        analysis_result = await pdf_service.analyze_and_summarize(extracted_text, difficulty)

        if not analysis_result.success:
            raise HTTPException(status_code=500, detail=analysis_result.error_message)

        logger.info("PDF 분석 완료")
        return analysis_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 분석 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"PDF 분석 중 오류가 발생했습니다: {str(e)}")

@router.post("/teacher/combine-topic", response_model=TopicCombineResult)
async def combine_topic_content(request: TopicCombineRequest):
    """PDF 내용과 직접 입력을 통합하여 최종 학습 주제를 생성합니다."""
    try:
        integration_service = get_topic_integration_service()

        result = await integration_service.combine_topic_sources(
            pdf_content=request.pdf_content,
            manual_content=request.manual_content,
            difficulty=request.difficulty
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)

        logger.info(f"주제 통합 완료: {result.source_type}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"주제 통합 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"주제 통합 중 오류가 발생했습니다: {str(e)}")

@router.post("/teacher/enhance-topic")
async def enhance_topic(
    content: str = Form(..., description="개선할 학습 내용"),
    difficulty: str = Form("normal", description="난이도")
):
    """단일 학습 내용을 소크라테스 대화에 더 적합하게 개선합니다."""
    try:
        integration_service = get_topic_integration_service()

        enhanced_content = await integration_service.enhance_single_topic(content, difficulty)

        return {
            "enhanced_content": enhanced_content,
            "success": True
        }

    except Exception as e:
        logger.error(f"주제 개선 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"주제 개선 중 오류가 발생했습니다: {str(e)}")

# 헬스체크 엔드포인트
@router.get("/teacher/pdf/health")
async def pdf_service_health():
    """PDF 서비스 상태 확인"""
    try:
        return {
            "status": "healthy",
            "service": "PDF Analysis Service",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"PDF 서비스 헬스체크 오류: {e}")
        raise HTTPException(status_code=500, detail="서비스가 정상적으로 동작하지 않습니다.")