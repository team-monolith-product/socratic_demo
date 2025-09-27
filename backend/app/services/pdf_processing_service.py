import io
import re
import logging
from typing import Optional, Dict, List
from fastapi import UploadFile, HTTPException
import PyPDF2
from openai import AsyncOpenAI
from app.core.config import get_settings
from app.models.pdf_models import PdfAnalysisResult

logger = logging.getLogger(__name__)

class PDFProcessingError(Exception):
    """PDF 처리 관련 오류"""
    pass

class PDFTooLargeError(PDFProcessingError):
    """PDF 파일 크기 초과"""
    pass

class PDFTextExtractionError(PDFProcessingError):
    """텍스트 추출 실패"""
    pass

class InvalidPDFContentError(PDFProcessingError):
    """부적절한 PDF 내용"""
    pass

class PDFProcessingService:
    """PDF 처리 및 분석 서비스"""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

        # PDF 처리 제한
        self.MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        self.MAX_PAGES = 50
        self.MAX_TEXT_LENGTH = 50000
        self.MIN_TEXT_LENGTH = 100

    async def extract_text_from_pdf(self, pdf_file: UploadFile) -> str:
        """PDF에서 텍스트 추출"""
        try:
            # 파일 크기 검증
            content = await pdf_file.read()
            if len(content) > self.MAX_FILE_SIZE:
                raise PDFTooLargeError(f"파일 크기가 너무 큽니다. (최대 {self.MAX_FILE_SIZE // (1024*1024)}MB)")

            # PDF 파일 검증
            if not pdf_file.content_type == "application/pdf":
                raise PDFProcessingError("PDF 파일만 업로드 가능합니다.")

            # PyPDF2로 텍스트 추출
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

            # 페이지 수 검증
            num_pages = len(pdf_reader.pages)
            if num_pages > self.MAX_PAGES:
                raise PDFProcessingError(f"페이지 수가 너무 많습니다. (최대 {self.MAX_PAGES}페이지)")

            # 전체 텍스트 추출
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"페이지 {page_num + 1} 텍스트 추출 실패: {e}")
                    continue

            # 추출된 텍스트 정리
            text = self._clean_extracted_text(text)

            # 텍스트 길이 검증
            if len(text) < self.MIN_TEXT_LENGTH:
                raise PDFTextExtractionError("텍스트를 충분히 추출할 수 없습니다. 다른 PDF를 시도해주세요.")

            if len(text) > self.MAX_TEXT_LENGTH:
                text = text[:self.MAX_TEXT_LENGTH] + "..."
                logger.info(f"텍스트가 너무 길어 {self.MAX_TEXT_LENGTH}자로 제한했습니다.")

            return text

        except (PDFProcessingError, PDFTooLargeError, PDFTextExtractionError):
            raise
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 오류: {e}")
            raise PDFTextExtractionError(f"PDF 처리 중 오류가 발생했습니다: {str(e)}")

    def _clean_extracted_text(self, text: str) -> str:
        """추출된 텍스트 정리"""
        # 불필요한 공백과 줄바꿈 제거
        text = re.sub(r'\n+', '\n', text)  # 연속된 줄바꿈을 하나로
        text = re.sub(r'[ \t]+', ' ', text)  # 연속된 공백을 하나로
        text = text.strip()

        # 특수 문자나 인코딩 문제 해결
        text = text.encode('utf-8', errors='ignore').decode('utf-8')

        return text

    async def validate_pdf_content(self, text: str) -> bool:
        """교육 콘텐츠로서의 적합성 검증"""
        try:
            # 기본 검증: 한국어 또는 영어 콘텐츠 확인
            korean_chars = len(re.findall(r'[가-힣]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            total_chars = len(text)

            if total_chars == 0:
                return False

            # 한국어나 영어가 전체의 30% 이상이면 유효한 콘텐츠로 판단
            readable_ratio = (korean_chars + english_chars) / total_chars
            if readable_ratio < 0.3:
                raise InvalidPDFContentError("읽을 수 있는 텍스트 내용이 부족합니다.")

            # 부적절한 콘텐츠 필터링 (기본적인 키워드 체크)
            inappropriate_keywords = ['성인', '도박', '불법', '폭력']
            text_lower = text.lower()

            for keyword in inappropriate_keywords:
                if keyword in text_lower:
                    logger.warning(f"부적절한 콘텐츠 감지: {keyword}")
                    # 일단은 경고만 하고 통과시킴 (교육용이므로 제한적 필터링)

            return True

        except InvalidPDFContentError:
            raise
        except Exception as e:
            logger.error(f"콘텐츠 검증 오류: {e}")
            return True  # 검증 오류시 기본적으로 허용

    async def analyze_and_summarize(self, text: str, difficulty: str) -> PdfAnalysisResult:
        """AI를 사용한 PDF 내용 분석 및 소크라테스식 학습 주제 생성"""
        try:
            system_prompt = f"""당신은 소크라테스식 교육법 전문가이자 학습 주제 설계자입니다.
주어진 PDF 자료를 바탕으로 학생들이 깊이 있게 탐구할 수 있는 실질적인 학습 주제를 개발하세요.

**임무**: PDF에서 추출한 핵심 내용을 바탕으로 소크라테스 대화에 적합한 학습 주제를 설계하세요.

**학습 주제 작성 가이드라인**:
1. PDF의 핵심 개념들을 활용하여 탐구 가능한 주제로 재구성
2. "~에 대해 설명하는 자료입니다" 형태가 아닌, 실제 학습할 내용을 명확히 제시
3. 학생들이 질문하고 토론할 수 있는 구체적인 학습 영역을 제시
4. 비판적 사고와 깊이 있는 탐구를 유도하는 방향으로 구성

**난이도별 접근**:
- easy: 기본 개념 이해와 실생활 연결에 중점
- normal: 개념 간 관계 파악과 응용에 중점
- hard: 심화 분석과 비판적 평가에 중점

현재 설정된 난이도: {difficulty}

**출력 형식**:
{{
    "summary": "학습 주제 설명 (PDF 내용을 바탕으로 한 구체적인 학습 내용, 5-8문단 분량으로 충분히 상세하게)",
    "key_concepts": ["핵심개념1", "핵심개념2", "핵심개념3", "핵심개념4", "핵심개념5"],
    "main_keyword": "가장_중요한_대표_키워드_하나 (PDF 전체를 가장 잘 표현하는 핵심 키워드)",
    "learning_objectives": ["구체적학습목표1", "구체적학습목표2", "구체적학습목표3"],
    "estimated_duration": 예상수업시간_분단위
}}

**주의사항**:
- summary는 단순한 PDF 요약이 아닌, 실제 수업에서 다룰 학습 주제 내용이어야 합니다
- 학생들이 "무엇을 배울 것인가"가 명확히 드러나야 합니다
- 탐구 질문과 토론 포인트가 자연스럽게 유발되는 내용이어야 합니다"""

            user_prompt = f"분석할 PDF 내용:\n\n{text[:8000]}..."  # OpenAI 토큰 제한 고려

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            # JSON 응답 파싱
            import json
            result_text = response.choices[0].message.content

            try:
                # JSON 부분만 추출
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                json_str = result_text[json_start:json_end]
                result_data = json.loads(json_str)
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"AI 응답 JSON 파싱 오류: {e}")
                # 파싱 실패시 기본 응답 생성
                result_data = {
                    "summary": result_text,
                    "key_concepts": [],
                    "main_keyword": "학습주제",
                    "learning_objectives": [],
                    "estimated_duration": 30
                }

            return PdfAnalysisResult(
                original_text=text,
                summary=result_data.get("summary", "요약 생성에 실패했습니다."),
                key_concepts=result_data.get("key_concepts", []),
                main_keyword=result_data.get("main_keyword", "학습주제"),
                learning_objectives=result_data.get("learning_objectives", []),
                estimated_duration=result_data.get("estimated_duration", 30),
                success=True,
                error_message=None
            )

        except Exception as e:
            logger.error(f"AI 분석 오류: {e}")
            return PdfAnalysisResult(
                original_text=text,
                summary="",
                key_concepts=[],
                main_keyword="오류",
                learning_objectives=[],
                estimated_duration=0,
                success=False,
                error_message=f"AI 분석 중 오류가 발생했습니다: {str(e)}"
            )

# 서비스 인스턴스 생성
_pdf_processing_service = None

def get_pdf_processing_service() -> PDFProcessingService:
    """PDF 처리 서비스 인스턴스 반환"""
    global _pdf_processing_service
    if _pdf_processing_service is None:
        _pdf_processing_service = PDFProcessingService()
    return _pdf_processing_service