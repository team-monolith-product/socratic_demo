"""
소크라테스식 다차원 평가 시스템

학생의 단순한 지식 이해도가 아닌, 소크라테스 산파법을 통한
사고의 질적 변화를 5차원으로 평가합니다.
"""

import json
from typing import Dict, List, Any

from openai import AsyncOpenAI

from app.core.config import get_settings

class SocraticAssessmentService:
    def __init__(self):
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        
        # 5차원 평가 가중치 (총합 100%)
        self.dimension_weights = {
            "depth": 0.25,        # 사고 깊이
            "breadth": 0.20,      # 사고 확장
            "application": 0.20,  # 실생활 적용
            "metacognition": 0.20,# 메타인지
            "engagement": 0.15    # 소크라테스적 참여
        }
        
        # 난이도별 완성 기준
        self.difficulty_criteria = {
            "easy": {
                "target_depth": 60,
                "target_breadth": 50,
                "target_application": 70,
                "target_metacognition": 40,
                "target_engagement": 50
            },
            "normal": {
                "target_depth": 75,
                "target_breadth": 70,
                "target_application": 75,
                "target_metacognition": 60,
                "target_engagement": 70
            },
            "hard": {
                "target_depth": 85,
                "target_breadth": 80,
                "target_application": 80,
                "target_metacognition": 80,
                "target_engagement": 85
            }
        }

    async def evaluate_socratic_dimensions(
        self, 
        topic: str, 
        student_response: str,
        ai_response: str,
        conversation_history: List[Dict],
        difficulty: str = "normal"
    ) -> Dict[str, Any]:
        """
        소크라테스식 5차원 평가 수행
        """
        
        # 대화 맥락 분석
        context_analysis = self._analyze_conversation_context(conversation_history)

        # 5차원 평가 프롬프트 생성 (system 지침 + user 대화 히스토리)
        system_prompt, user_prompt = self._build_multidimensional_prompt(
            topic, student_response, ai_response, context_analysis, difficulty
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            # AI 응답 내용 확인
            response_content = response.choices[0].message.content.strip()
            print(f"🤖 AI 평가 응답 원본: {response_content[:200]}...")
            
            # JSON 응답 파싱
            evaluation_result = json.loads(response_content)
            
            # 종합 점수 계산
            overall_score = self._calculate_weighted_score(evaluation_result["dimensions"])
            
            # 완성도 체크
            is_completed = self._check_completion_criteria(
                evaluation_result["dimensions"], difficulty
            )
            
            print(f"✅ 5차원 평가 완료 - 종합점수: {overall_score}")
            
            return {
                "dimensions": evaluation_result["dimensions"],
                "overall_score": overall_score,
                "is_completed": is_completed,
                "insights": evaluation_result["insights"],
                "growth_indicators": evaluation_result["growth_indicators"],
                "next_focus": evaluation_result["next_focus"]
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            print(f"🔍 AI 응답 내용: {response.choices[0].message.content}")
            return self._get_default_evaluation()
        except Exception as e:
            print(f"❌ 평가 오류: {e}")
            return self._get_default_evaluation()

    def _analyze_conversation_context(self, conversation_history: List[Dict]) -> Dict:
        """대화 맥락 분석"""
        if not conversation_history:
            return {
                "turn_count": 0,
                "question_evolution": [],
                "concept_progression": [],
                "full_conversation": []
            }

        # 대화 턴 수
        turn_count = len([msg for msg in conversation_history if msg.get("role") == "user"])

        # 질문의 진화 패턴
        user_messages = [msg["content"] for msg in conversation_history if msg.get("role") == "user"]

        # 개념 이해의 진행 과정
        concept_progression = self._extract_concept_progression(user_messages)

        return {
            "turn_count": turn_count,
            "question_evolution": user_messages,
            "concept_progression": concept_progression,
            "conversation_depth": min(turn_count * 10, 50),  # 대화 깊이 보너스
            "full_conversation": conversation_history  # 전체 대화 포함
        }

    def _extract_concept_progression(self, messages: List[str]) -> List[str]:
        """학생 답변에서 개념 이해의 진행 과정 추출"""
        progressions = []
        for i, msg in enumerate(messages):
            if len(msg) > 20:  # 의미있는 답변만
                stage = "초기" if i < 3 else "중기" if i < 6 else "심화"
                progressions.append(f"{stage}: {msg[:50]}...")
        return progressions

    def _build_conversation_summary(self, conversation_history: List[Dict]) -> str:
        """전체 대화 과정(AI 질문 + 학생 답변)을 요약하여 맥락 제공"""
        if not conversation_history:
            return "대화가 시작되지 않았습니다."

        summary_parts = []
        turn_number = 0

        for msg in conversation_history:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "assistant":
                # AI의 소크라테스식 질문
                truncated_content = content[:200] + "..." if len(content) > 200 else content
                turn_number += 1
                summary_parts.append(f"\n[턴 {turn_number} - AI 질문]")
                summary_parts.append(f"{truncated_content}")
            elif role == "user":
                # 학생의 답변
                truncated_content = content[:200] + "..." if len(content) > 200 else content
                summary_parts.append(f"\n[턴 {turn_number} - 학생 답변]")
                summary_parts.append(f"{truncated_content}")

        return "\n".join(summary_parts)

    def _build_multidimensional_prompt(
        self,
        topic: str,
        student_response: str,
        ai_response: str,
        context: Dict,
        difficulty: str
    ) -> tuple[str, str]:
        """5차원 평가를 위한 프롬프트 생성 (system 지침, user 대화 히스토리)"""

        criteria = self.difficulty_criteria[difficulty]

        # 전체 대화 내용(AI 질문 + 학생 답변)을 맥락으로 포함
        conversation_summary = self._build_conversation_summary(context.get('full_conversation', []))

        # System 메시지: 평가 지침
        system_prompt = """당신은 소크라테스식 5차원 평가 전문가입니다.

**평가 원칙**:
- 학생의 최신 답변만이 아니라, 전체 대화 과정을 통해 나타난 학습자의 누적된 이해도와 성장을 종합적으로 평가하세요
- 대화가 진행될수록 점수는 점진적으로 상승해야 합니다
- 한 번 달성한 이해도는 쉽게 후퇴하지 않습니다
- 급격한 점수 변동보다는 안정적인 성장을 반영하세요
- 학습자의 전반적인 발전 궤도를 고려하세요

**5차원 평가 기준**:
1. 사고 깊이 (0-100): 표면적 → 본질적 이해 (누적적 평가)
2. 사고 확장 (0-100): 단일 → 다각적 관점 (누적적 평가)
3. 실생활 적용 (0-100): 추상적 → 구체적 연결 (누적적 평가)
4. 메타인지 (0-100): 사고 과정 인식 (누적적 평가)
5. 소크라테스적 참여 (0-100): 수동적 → 능동적 탐구 (누적적 평가)

**응답 형식**:
반드시 아래 JSON 형식으로만 응답하세요:

{
    "dimensions": {
        "depth": 점수,
        "breadth": 점수,
        "application": 점수,
        "metacognition": 점수,
        "engagement": 점수
    },
    "insights": {
        "depth": "깊이 평가 설명",
        "breadth": "확장 평가 설명",
        "application": "적용 평가 설명",
        "metacognition": "메타인지 평가 설명",
        "engagement": "참여 평가 설명"
    },
    "growth_indicators": ["성장지표1", "성장지표2"],
    "next_focus": "다음 학습 방향 제안"
}"""

        # User 메시지: 대화 히스토리
        user_prompt = f"""주제: {topic}
난이도: {difficulty}
대화 턴: {context['turn_count']}회

전체 대화 과정:
{conversation_summary}

학생의 최신 답변: "{student_response}"

위 대화를 종합적으로 분석하여 5차원 평가를 수행해주세요."""

        return system_prompt, user_prompt

    def _calculate_weighted_score(self, dimensions: Dict[str, int]) -> int:
        """가중치를 적용한 종합 점수 계산"""
        total_score = 0
        for dimension, score in dimensions.items():
            weight = self.dimension_weights.get(dimension, 0)
            total_score += score * weight
        
        return int(total_score)

    def _check_completion_criteria(self, dimensions: Dict[str, int], difficulty: str) -> bool:
        """완성 기준 체크"""
        criteria = self.difficulty_criteria[difficulty]
        
        return (
            dimensions.get("depth", 0) >= criteria["target_depth"] and
            dimensions.get("breadth", 0) >= criteria["target_breadth"] and
            dimensions.get("application", 0) >= criteria["target_application"] and
            dimensions.get("metacognition", 0) >= criteria["target_metacognition"] and
            dimensions.get("engagement", 0) >= criteria["target_engagement"]
        )

    def _get_default_evaluation(self) -> Dict[str, Any]:
        """오류 시 기본 평가 반환"""
        return {
            "dimensions": {
                "depth": 30,
                "breadth": 25,
                "application": 20,
                "metacognition": 15,
                "engagement": 35
            },
            "overall_score": 25,
            "is_completed": False,
            "insights": {
                "depth": "평가 중 오류가 발생했습니다.",
                "breadth": "",
                "application": "",
                "metacognition": "",
                "engagement": ""
            },
            "growth_indicators": ["대화를 계속 진행해주세요."],
            "next_focus": "함께 탐구를 이어가봅시다."
        }

    def get_dimension_feedback(self, dimensions: Dict[str, int]) -> str:
        """차원별 피드백 메시지 생성"""
        total = sum(dimensions.values()) / len(dimensions)
        
        if total >= 80:
            return "🌟 탁월한 소크라테스적 사고를 보여주고 있습니다!"
        elif total >= 60:
            return "🧠 사고가 깊어지고 확장되고 있어요!"
        elif total >= 40:
            return "💡 좋은 진전을 보이고 있습니다!"
        else:
            return "🌱 함께 탐구의 여정을 시작해봅시다!"

# 서비스 인스턴스 생성 함수
def get_socratic_assessment_service():
    return SocraticAssessmentService()
