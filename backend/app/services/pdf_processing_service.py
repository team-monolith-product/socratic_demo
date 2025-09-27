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

        # PDF 처리 제한 (파일 크기는 10MB로 완화)
        self.MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB 유지
        self.MAX_PAGES = 30  # 30 페이지 유지
        self.MAX_TEXT_LENGTH = 5000  # 5000자 유지
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
        """AI를 사용한 PDF 내용 압축 및 소크라테스식 학습 주제 생성 (통합)"""
        try:
            # 기본 정리
            cleaned_text = self._clean_extracted_text(text)

            # AI를 사용한 압축 + 한 문장 학습 주제 생성 (한 번에 수행)
            system_prompt = f"""당신은 소크라테스식 교육법 전문가입니다.
주어진 PDF 자료를 압축하고 학습 주제를 한 문장으로 요약하는 두 가지 작업을 수행하세요.

**작업 1: PDF 내용 압축**
다음 규칙에 따라 교육 자료를 압축하세요:
1. 핵심 개념과 정의는 반드시 유지
2. 중요한 예시와 설명은 간략하게 유지
3. 반복되는 내용은 하나만 남김
4. 학습 목표와 관련 없는 부가 정보 제거
5. 전체적인 흐름과 구조는 유지
6. 압축 후에도 소크라테스 대화가 가능하도록 충분한 내용 유지

**작업 2: 한 문장 학습 주제 생성**
PDF 내용의 핵심을 파악하여 소크라테스 대화에 적합한 한 문장 학습 주제를 생성하세요:
1. PDF의 가장 중요한 핵심 내용을 한 문장으로 압축
2. 학생들이 즉시 이해할 수 있는 명확하고 간결한 표현
3. 소크라테스식 질문과 탐구를 유발할 수 있는 주제
4. "~에 대해 설명하는 자료" 형태가 아닌 실제 학습할 내용

**난이도별 접근**:
- easy: 기본 개념 중심의 친근한 표현
- normal: 개념 간 관계를 암시하는 표현
- hard: 비판적 사고를 유도하는 도전적 표현

현재 설정된 난이도: {difficulty}

**출력 형식**:
{{
    "compressed_content": "압축된 PDF 전문",
    "one_sentence_topic": "한 문장으로 표현한 핵심 학습 주제"
}}

**주의사항**:
- compressed_content는 학습에 필요한 핵심 내용만 압축된 전문
- one_sentence_topic은 반드시 한 문장으로 제한하며, UI에 바로 노출 가능한 수준으로 작성"""

            # 토큰 제한을 고려한 컨텍스트 크기 조정 (GPT-4o-mini 8K 토큰 제한)
            # 시스템 프롬프트 + 사용자 프롬프트 + 응답을 고려하여 더 안전한 크기로 설정
            max_content_length = 2000  # 3000 -> 2000자로 더 축소하여 안정성 확보
            if len(cleaned_text) > max_content_length:
                cleaned_text = cleaned_text[:max_content_length] + "..."

            user_prompt = f"""PDF 내용:
{cleaned_text}

위 내용을 압축하고 소크라테스 학습 주제를 설계해주세요."""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # 통합 처리를 위해 GPT-4o-mini 사용
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000  # 배포 환경 안정성을 위해 토큰 수 줄임
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
                    "compressed_content": cleaned_text[:2000] + "..." if len(cleaned_text) > 2000 else cleaned_text,
                    "one_sentence_topic": "학습 주제"
                }

            return PdfAnalysisResult(
                original_text=text,
                compressed_content=result_data.get("compressed_content", cleaned_text[:1000] + "..." if len(cleaned_text) > 1000 else cleaned_text),
                one_sentence_topic=result_data.get("one_sentence_topic", "학습 주제"),
                success=True,
                error_message=None
            )

        except Exception as e:
            logger.error(f"AI 분석 오류: {e}")
            # 배포 환경에서 안정적인 폴백 제공
            fallback_compressed = cleaned_text[:1000] + "..." if len(cleaned_text) > 1000 else cleaned_text
            return PdfAnalysisResult(
                original_text=text,
                compressed_content=fallback_compressed,
                one_sentence_topic="업로드된 PDF 자료를 바탕으로 한 학습 주제",
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