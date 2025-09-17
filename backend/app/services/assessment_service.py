from openai import AsyncOpenAI
import re
from typing import List, Dict

from app.core.config import get_settings

class AssessmentService:
    def __init__(self):
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def evaluate_understanding(self, topic: str, user_message: str, ai_response: str, current_level: int, difficulty: str = "normal", conversation_history: list = None) -> int:
        """사용자의 이해도를 0-100점으로 평가 (상승 50%까지, 하락 5%까지 제한)"""
        
        # 대화 기록 포함
        conversation_context = ""
        if conversation_history and len(conversation_history) > 1:
            conversation_context = "\n# 대화 기록 (참고용):\n"
            for i, msg in enumerate(conversation_history[-6:], 1):  # 최근 6개 메시지만
                role = "학생" if msg.get("role") == "user" else "AI"
                conversation_context += f"{i}. {role}: {msg.get('content', '')[:100]}...\n"
        
        # 난이도별 평가 기준 설정
        difficulty_settings = {
            "easy": {
                "level_desc": "초등학교 고학년 수준",
                "completion_criteria": "기본 개념을 이해하고 간단한 예시를 들 수 있으면 완성",
                "max_increase": 0.6,  # 60%까지 상승
                "max_decrease": 0.03  # 3%까지 하락
            },
            "normal": {
                "level_desc": "중학생 수준", 
                "completion_criteria": "핵심 개념을 이해하고 관련 개념과 연결지을 수 있으면 완성",
                "max_increase": 0.5,  # 50%까지 상승
                "max_decrease": 0.05  # 5%까지 하락
            },
            "hard": {
                "level_desc": "고등학생 이상 수준",
                "completion_criteria": "깊이 있는 이해와 비판적 사고, 창의적 적용이 가능해야 완성",
                "max_increase": 0.4,  # 40%까지 상승
                "max_decrease": 0.07  # 7%까지 하락
            }
        }
        
        setting = difficulty_settings.get(difficulty, difficulty_settings["normal"])
        
        evaluation_prompt = f"""
당신은 교육 전문가입니다. 다음 학습 주제에 대한 학생의 이해도를 평가해주세요.

# 학습 주제: {topic}
# 난이도: {difficulty} ({setting['level_desc']})
# 현재 이해도: {current_level}점
{conversation_context}
# 학생의 최신 응답: "{user_message}"

**평가 원칙**: 
1. 현재 점수는 {current_level}점입니다.
2. 대화 전체를 고려하여 누적 이해도를 평가합니다.
3. 점수 변동 제한: 상승 최대 {int(setting['max_increase']*100)}점, 하락 최대 {int(setting['max_decrease']*100)}점
4. {difficulty} 난이도 완성 기준: {setting['completion_criteria']}

## 절대적 평가 기준 (엄격히 적용):

### 0-20점: 전혀 모르거나 완전히 틀림
- "모르겠어요", "처음 들어봐요" 등
- 주제와 완전히 무관한 답변
- 명백히 잘못된 정보

### 21-40점: 용어만 아는 기초 수준  
- 주제 이름은 들어봤으나 설명 못함
- 매우 기초적이고 부정확한 설명
- 피상적 지식만 보임

### 41-60점: 기본 개념 이해
- 기본적인 개념을 어느 정도 설명 가능
- 정확하지만 깊이가 부족한 답변
- 단순한 예시 정도만 제시

### 61-80점: 충분한 이해와 연결
- 핵심 개념을 정확하고 체계적으로 설명
- 관련 개념들과의 연결 보여줌
- 적절한 예시나 적용 사례 제시

### 81-100점: 전문가 수준의 깊은 이해
- 복합적이고 창의적인 사고 보여줌
- 비판적 분석이나 새로운 관점 제시
- 고급 수준의 적용이나 통찰

## 점수 조정 규칙:
- 우수한 답변: +3~{int(setting['max_increase']*100)}점 (최대 상승)
- 보통 답변: +1~2점
- 부족한 답변: 0점 또는 -1점
- 잘못된 이해: -1~{int(setting['max_decrease']*100)}점 (최대 하락)

## 필수 출력 형식:
점수: [0-100 사이의 정수]
근거: [평가 근거를 간단히 설명]

**중요**: 현재 {current_level}점에서 최대 +{int(setting['max_increase']*100)}점 / -{int(setting['max_decrease']*100)}점까지만 변동 가능합니다.
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": evaluation_prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            print(f"🔍 AI 평가 응답: {result}")  # 디버깅용
            
            # 점수 추출 및 조정기 적용
            score_match = re.search(r'점수:\s*(\d+)', result)
            if score_match:
                ai_suggested_score = int(score_match.group(1))
                
                # 난이도별 점수 변동 제한 적용
                max_increase = int(setting['max_increase'] * 100)
                max_decrease = int(setting['max_decrease'] * 100)
                
                # 변동 제한 계산
                max_allowed = current_level + max_increase
                min_allowed = max(0, current_level - max_decrease)
                
                # 점수 조정기 적용
                final_score = max(min_allowed, min(max_allowed, ai_suggested_score))
                final_score = max(0, min(100, final_score))  # 0-100 범위 제한
                
                print(f"📊 {difficulty} 난이도 - AI 제안: {ai_suggested_score}, 이전: {current_level}, 범위: {min_allowed}-{max_allowed}, 최종: {final_score}")
                
                return final_score
            else:
                print(f"❌ 점수 추출 실패, 현재 점수 유지: {current_level}")
                return current_level
                
        except Exception as e:
            print(f"Assessment error: {e}")
            # 오류 시 현재 점수 유지
            return current_level
    
    async def generate_progress_feedback(self, topic: str, understanding_score: int) -> str:
        """이해도에 따른 학습 진행도 피드백 생성"""
        
        if understanding_score <= 20:
            level = "탐구 시작"
            feedback = "이제 막 탐구를 시작했어요! 함께 알아가봐요 🌱"
        elif understanding_score <= 40:
            level = "기초 이해"
            feedback = "기본적인 이해가 생겼어요! 더 깊이 들어가볼까요? 💡"
        elif understanding_score <= 60:
            level = "초급 수준"
            feedback = "개념을 잘 이해하고 있어요! 연결고리를 찾아보세요 🔗"
        elif understanding_score <= 80:
            level = "중급 수준"
            feedback = "훌륭한 이해력이에요! 비판적 사고를 시작해보세요 🧠"
        else:
            level = "고급 수준"
            feedback = "전문가 수준의 깊은 이해를 보여주고 있어요! 🌟"
        
        return f"{level}: {feedback}"
