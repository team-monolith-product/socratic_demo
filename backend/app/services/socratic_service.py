from openai import AsyncOpenAI
from typing import List, Dict

from app.core.config import get_settings

class SocraticService:
    def __init__(self):
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def validate_topic(self, topic_content: str) -> bool:
        """주제의 교육적 적합성 검증"""
        validation_prompt = f"""
다음 학습 주제가 중학생에게 교육적으로 적합한지 판단해주세요:

주제: {topic_content}

판단 기준:
1. 중학생 수준에 적합한가?
2. 교육적 가치가 있는가?
3. 소크라테스식 대화로 탐구 가능한가?
4. 안전하고 건전한 내용인가?

적합하면 "YES", 부적합하면 "NO"만 답변하세요.
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": validation_prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().upper()
            return result == "YES"
            
        except Exception as e:
            print(f"Topic validation error: {e}")
            return False
    
    async def generate_initial_message(self, topic: str) -> str:
        """주제 기반 첫 대화 메시지 생성"""
        system_prompt = self._build_socratic_system_prompt(topic)
        
        initial_prompt = f"""
학생이 '{topic}' 주제로 학습을 시작합니다. 
소크라테스식 산파법에 따라 첫 대화를 시작해주세요.

규칙:
1. 학생의 기존 지식을 탐구하는 질문으로 시작
2. 친근하고 격려하는 어조
3. 답을 직접 제공하지 말고 사고를 유도
4. 중학생 수준에 맞는 언어 사용
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": initial_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Initial message generation error: {e}")
            return f"안녕하세요! 오늘은 '{topic}'에 대해 함께 탐구해볼까요? 먼저 이 주제에 대해 어떤 생각이 드시나요?"
    
    async def generate_socratic_response(self, topic: str, messages: List[Dict], understanding_level: int) -> str:
        """소크라테스식 응답 생성"""
        system_prompt = self._build_socratic_system_prompt(topic, understanding_level)
        
        try:
            # 대화 히스토리 구성
            conversation_messages = [{"role": "system", "content": system_prompt}]
            
            for msg in messages:
                role = "user" if msg["role"] == "user" else "assistant"
                conversation_messages.append({"role": role, "content": msg["content"]})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=conversation_messages,
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Socratic response generation error: {e}")
            return "죄송해요, 일시적인 오류가 발생했습니다. 다시 말씀해 주세요."
    
    def _build_socratic_system_prompt(self, topic: str, understanding_level: int = 0) -> str:
        """소크라테스식 산파법 시스템 프롬프트 구축"""
        
        # 이해도 수준에 따른 접근 방식 조정
        if understanding_level < 30:
            approach = "기본 개념 탐구와 예시 중심"
        elif understanding_level < 70:
            approach = "연결과 비교, 심화 질문"
        else:
            approach = "창의적 적용과 종합적 사고"
        
        return f"""# 소크라테스식 AI 튜터 시스템 V2.0

## 역할 정의
당신은 소크라테스의 산파법(MAIEUTICS)을 완벽히 구현하는 AI 교육 전문가입니다. 
당신의 핵심 임무는 학생이 스스로 지식을 '출산'하도록 돕는 것입니다. 
대상은 중학교 학년 학생들입니다. '{topic}'에 대해 배우고 있습니다.

## 핵심 교육 철학
- 직접적 답변 절대 금지: 학생의 비판적 사고를 AI에 맡기지 않음
- 무지의 고백: "나도 확실하지 않으니 함께 탐구해보자"는 태도 유지
- 점층적 탐구: 단계별로 깊이를 더해가며 질문 구체화
- 생산적 불편함: 적절한 인지적 도전을 통한 성장 유도

## 질문 전략 체계 (6단계)
1단계: 명확화 질문 - "정확히 무엇을 의미하나요?"
2단계: 가정 탐구 질문 - "어떤 가정에 기반하고 있나요?"
3단계: 근거 확인 질문 - "그렇게 생각하는 이유는 무엇인가요?"
4단계: 관점 탐색 질문 - "다른 관점에서 보면 어떨까요?"
5단계: 함의 분석 질문 - "그렇다면 어떤 결과가 나올까요?"
6단계: 메타인지 질문 - "지금까지의 사고 과정을 돌아보면?"

## 현재 학습 접근법
현재 이해도: {understanding_level}%
권장 접근법: {approach}

## 대화 진행 규칙
- 한 번에 하나의 질문만
- 학생 답변의 키워드를 활용해 후속 질문
- 단계별로 천천히 심화
- 격려와 칭찬 표현 사용
- 중학생 수준의 쉬운 언어 사용

## 학습 주제 집중
주제: {topic}
- 항상 이 주제와 연관지어 질문하고 응답
- 주제에서 벗어나면 부드럽게 돌려보내기
- 주제의 핵심 개념들을 점진적으로 탐구
"""
