import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import get_settings
from app.models.pdf_models import TopicCombineResult

logger = logging.getLogger(__name__)

class TopicIntegrationService:
    """PDF 내용과 직접 입력을 통합하는 서비스"""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def combine_topic_sources(
        self,
        pdf_content: Optional[str] = None,
        manual_content: Optional[str] = None,
        difficulty: str = "normal"
    ) -> TopicCombineResult:
        """PDF 분석 결과와 직접 입력을 통합한 최종 학습 주제 생성"""
        try:
            # 입력 상황 파악
            source_type = self._determine_source_type(pdf_content, manual_content)

            if source_type == "manual":
                # 직접 입력만 있는 경우
                return TopicCombineResult(
                    combined_topic=manual_content.strip(),
                    source_type=source_type,
                    success=True
                )
            elif source_type == "pdf":
                # PDF만 있는 경우
                return TopicCombineResult(
                    combined_topic=pdf_content.strip(),
                    source_type=source_type,
                    success=True
                )
            elif source_type == "hybrid":
                # 둘 다 있는 경우 - AI로 통합
                combined_topic = await self._generate_combined_topic(
                    pdf_content, manual_content, difficulty
                )
                return TopicCombineResult(
                    combined_topic=combined_topic,
                    source_type=source_type,
                    success=True
                )
            else:
                return TopicCombineResult(
                    combined_topic="",
                    source_type="none",
                    success=False,
                    error_message="학습 주제를 위한 내용이 제공되지 않았습니다."
                )

        except Exception as e:
            logger.error(f"주제 통합 오류: {e}")
            return TopicCombineResult(
                combined_topic="",
                source_type="error",
                success=False,
                error_message=f"주제 통합 중 오류가 발생했습니다: {str(e)}"
            )

    def _determine_source_type(self, pdf_content: Optional[str], manual_content: Optional[str]) -> str:
        """입력 상황에 따른 소스 타입 결정"""
        has_pdf = pdf_content and pdf_content.strip()
        has_manual = manual_content and manual_content.strip()

        if has_pdf and has_manual:
            return "hybrid"
        elif has_pdf:
            return "pdf"
        elif has_manual:
            return "manual"
        else:
            return "none"

    async def _generate_combined_topic(
        self,
        pdf_content: str,
        manual_content: str,
        difficulty: str
    ) -> str:
        """AI를 사용해 PDF와 직접 입력을 통합한 학습 주제 생성"""
        try:
            system_prompt = f"""당신은 교육 과정 설계 전문가입니다.
PDF 분석 결과와 교사의 직접 입력을 통합하여 완전한 소크라테스 학습 주제를 생성하세요:

전략:
1. PDF 내용을 메인 주제로 사용
2. 직접 입력을 보조 맥락이나 추가 관점으로 활용
3. 두 내용을 자연스럽게 연결하여 통합된 학습 주제 생성
4. 소크라테스식 질문과 탐구를 위한 구조로 작성
5. 최종 결과는 3-4개 문단으로 구성

난이도: {difficulty}

통합 원칙:
- PDF의 핵심 내용을 기반으로 함
- 교사의 추가 관점을 의미있게 연결
- 일관성 있는 학습 흐름 유지
- 소크라테스식 대화에 적합한 주제로 완성"""

            user_prompt = f"""PDF 분석 내용:
{pdf_content}

교사 추가 입력:
{manual_content}

위 두 내용을 자연스럽게 통합하여 완전한 학습 주제를 생성해주세요."""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            combined_topic = response.choices[0].message.content.strip()

            # 결과가 너무 짧으면 기본 결합 방식 사용
            if len(combined_topic) < 100:
                combined_topic = f"{pdf_content}\n\n{manual_content}"

            return combined_topic

        except Exception as e:
            logger.error(f"AI 통합 생성 오류: {e}")
            # AI 실패시 간단한 결합
            return f"{pdf_content}\n\n추가 관점: {manual_content}"

    async def enhance_single_topic(self, content: str, difficulty: str) -> str:
        """단일 입력 내용을 소크라테스 대화에 더 적합하게 개선"""
        try:
            if not content or not content.strip():
                return ""

            # 이미 충분히 길고 구조화되어 있으면 그대로 반환
            if len(content) > 200 and '문단' in content:
                return content.strip()

            system_prompt = f"""당신은 소크라테스식 대화 전문가입니다.
주어진 학습 내용을 소크라테스식 탐구와 대화에 더 적합하도록 개선하세요:

개선 원칙:
1. 학생들의 호기심과 질문을 유발할 수 있도록 구성
2. 탐구할 수 있는 논점과 관점 포함
3. 토론과 비판적 사고를 촉진하는 내용으로 확장
4. 3-4개 문단으로 구조화

난이도: {difficulty}"""

            user_prompt = f"개선할 학습 내용:\n{content}"

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            enhanced_content = response.choices[0].message.content.strip()
            return enhanced_content if enhanced_content else content

        except Exception as e:
            logger.error(f"단일 주제 개선 오류: {e}")
            return content  # 개선 실패시 원본 반환

# 서비스 인스턴스 생성
_topic_integration_service = None

def get_topic_integration_service() -> TopicIntegrationService:
    """주제 통합 서비스 인스턴스 반환"""
    global _topic_integration_service
    if _topic_integration_service is None:
        _topic_integration_service = TopicIntegrationService()
    return _topic_integration_service