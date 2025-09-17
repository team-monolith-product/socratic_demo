# LLM Classroom Proto4 - 기술문서

## 📋 개요

**LLM Classroom Proto4**는 소크라테스의 산파법을 AI로 구현한 혁신적인 교육 플랫폼입니다. 중학생들이 자기주도적 학습을 통해 비판적 사고력을 기를 수 있도록 설계된 차세대 에듀테크 솔루션입니다.

### 🎯 핵심 기능
- **소크라테스식 AI 튜터**: 6단계 질문 전략 기반 대화형 학습
- **실시간 이해도 평가**: 듀얼 AI 시스템으로 정확한 학습 진도 측정
- **개인맞춤형 학습**: 난이도별 적응형 학습 환경
- **직관적 UI/UX**: 모던한 세그먼트 컨트롤 및 반응형 디자인

---

## 🏗 시스템 아키텍처

### 전체 구조도
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │────▶│  OpenAI API     │
│   (Vanilla JS)  │     │   (FastAPI)     │     │  GPT-4o-mini    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                        ┌──────┴──────┐
                        │             │
                  ┌─────▼─────┐ ┌─────▼─────┐
                  │ Socratic  │ │Assessment │
                  │    AI     │ │    AI     │
                  └───────────┘ └───────────┘
```

### 기술 스택
- **Backend**: FastAPI (Python 3.11)
- **AI Model**: OpenAI GPT-4o-mini  
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **웹서버**: Uvicorn
- **Architecture**: RESTful API, Microservice Pattern

---

## 📁 프로젝트 구조

```
proto4/
├── backend/
│   ├── app/
│   │   ├── api/                    # API 엔드포인트
│   │   │   └── socratic_chat.py    # 메인 채팅 API
│   │   ├── services/               # 비즈니스 로직
│   │   │   ├── socratic_service.py # 소크라테스 AI 서비스
│   │   │   └── assessment_service.py # 이해도 평가 서비스
│   │   ├── models/                 # 데이터 모델
│   │   │   └── request_models.py   # API 요청/응답 모델
│   │   └── __init__.py
│   ├── main.py                     # FastAPI 애플리케이션
│   ├── requirements.txt            # Python 의존성
│   └── .env                        # 환경 변수
├── frontend/
│   ├── index.html                  # 주제 입력 페이지
│   ├── pages/
│   │   └── socratic-chat.html      # 채팅 인터페이스
│   └── static/
│       ├── css/                    # 스타일시트
│       │   ├── main.css            # 메인 페이지 스타일
│       │   └── chat.css            # 채팅 페이지 스타일
│       └── js/                     # JavaScript
│           ├── main.js             # 메인 페이지 로직
│           └── chat.js             # 채팅 페이지 로직
├── USER_GUIDE.md                   # 사용자 가이드
├── TECHNICAL_DOCUMENTATION.md      # 기술 문서
├── PROMPT_DOCUMENTATION.md         # 프롬프트 가이드
└── README.md                       # 프로젝트 개요
```

---

## 🔌 API 엔드포인트

### 1. 주제 검증 API
```http
POST /api/v1/topic/validate
Content-Type: application/json

{
  "topic_content": "유니버설 디자인의 개념과 실생활 적용",
  "content_type": "text"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "학습 주제가 설정되었습니다."
}
```

### 2. 초기 메시지 생성 API
```http
POST /api/v1/chat/initial
Content-Type: application/json

{
  "topic": "유니버설 디자인",
  "difficulty": "normal"
}
```

**Response:**
```json
{
  "initial_message": "안녕하세요! 유니버설 디자인에 대해 먼저 어떤 생각이 드시나요?",
  "understanding_score": 0
}
```

### 3. 소크라테스식 대화 API  
```http
POST /api/v1/chat/socratic
Content-Type: application/json

{
  "topic": "유니버설 디자인",
  "messages": [
    {"role": "user", "content": "모든 사람이 사용할 수 있는 디자인이에요"},
    {"role": "assistant", "content": "좋은 시작이네요! 그런데..."}
  ],
  "understanding_level": 25,
  "difficulty": "normal"
}
```

**Response:**
```json
{
  "socratic_response": "그렇다면 '모든 사람'이라는 것은 구체적으로 누구를 의미할까요?",
  "understanding_score": 35,
  "is_completed": false
}
```

---

## 🤖 AI 서비스 아키텍처

### 1. 소크라테스 AI 서비스 (`socratic_service.py`)

#### 핵심 기능:
- **주제 검증**: 교육적 적합성 및 안전성 확인
- **초기 메시지 생성**: 주제별 맞춤 첫 질문 생성
- **소크라테스식 응답**: 6단계 질문 전략 적용

#### 6단계 질문 전략:
1. **명확화 질문**: "정확히 무엇을 의미하나요?"
2. **가정 탐구**: "어떤 가정에 기반하고 있나요?"  
3. **근거 확인**: "그렇게 생각하는 이유는 무엇인가요?"
4. **관점 탐색**: "다른 관점에서 보면 어떨까요?"
5. **함의 분석**: "그렇다면 어떤 결과가 나올까요?"
6. **메타인지**: "지금까지의 사고 과정을 돌아보면?"

#### 난이도별 시스템 프롬프트:
```python
def _build_socratic_system_prompt(self, topic: str, difficulty: str, understanding_level: int = 0) -> str:
    approach_map = {
        "easy": "기본 개념 탐구와 예시 중심",
        "normal": "연결과 비교, 심화 질문", 
        "hard": "창의적 적용과 종합적 사고"
    }
    
    return f"""
    # 소크라테스식 AI 튜터 시스템 V2.0
    
    ## 역할 정의  
    당신은 소크라테스의 산파법을 구현하는 AI 교육 전문가입니다.
    대상: 중학생, 주제: {topic}, 난이도: {difficulty}
    
    ## 현재 학습 접근법
    이해도: {understanding_level}%
    권장 접근법: {approach_map.get(difficulty, "연결과 비교, 심화 질문")}
    
    ## 핵심 교육 철학
    - 직접적 답변 절대 금지
    - 무지의 고백: "함께 탐구해보자"
    - 점층적 탐구: 단계별 질문 심화
    - 생산적 불편함: 적절한 인지적 도전
    """
```

### 2. 이해도 평가 AI 서비스 (`assessment_service.py`)

#### 핵심 기능:
- **실시간 이해도 평가**: 0-100점 연속 척도
- **대화 맥락 분석**: 최근 6개 메시지 고려
- **난이도별 점수 조정**: 개인맞춤형 평가 기준

#### 난이도별 점수 변동 제한:
```python
difficulty_settings = {
    "easy": {
        "max_increase": 0.6,  # 60%까지 상승
        "max_decrease": 0.03, # 3%까지 하락
        "completion_criteria": "기본 개념 + 간단한 예시"
    },
    "normal": {
        "max_increase": 0.5,  # 50%까지 상승  
        "max_decrease": 0.05, # 5%까지 하락
        "completion_criteria": "핵심 개념 + 관련 개념 연결"
    },
    "hard": {
        "max_increase": 0.4,  # 40%까지 상승
        "max_decrease": 0.07, # 7%까지 하락  
        "completion_criteria": "깊이 있는 이해 + 비판적 사고 + 창의적 적용"
    }
}
```

#### 5단계 평가 기준:
- **0-20점**: 전혀 모르거나 완전히 틀림
- **21-40점**: 용어만 아는 기초 수준  
- **41-60점**: 기본 개념 이해
- **61-80점**: 충분한 이해와 연결
- **81-100점**: 전문가 수준의 깊은 이해

---

## 🎨 프론트엔드 아키텍처

### 1. 모듈별 구조

#### **주제 입력 페이지 (`index.html` + `main.js`)**
- **세그먼트 컨트롤 UI**: 입력방식/난이도/진행도 선택
- **주제 검증**: 서버사이드 검증 후 채팅 페이지 이동
- **반응형 디자인**: 데스크톱/모바일 적응형 레이아웃

#### **채팅 인터페이스 (`socratic-chat.html` + `chat.js`)**
- **실시간 채팅**: WebSocket 없이 HTTP 폴링 방식
- **이해도 게이지**: 실시간 점수 시각화
- **완료 축하**: 100점 달성시 애니메이션

### 2. 핵심 JavaScript 클래스

#### **SocraticChatHandler 클래스:**
```javascript
class SocraticChatHandler {
    constructor() {
        this.apiBase = 'http://localhost:8000/api/v1';
        this.topic = '';
        this.difficulty = 'normal';
        this.messages = [];
        this.understandingScore = 0;
        this.showScore = true;
        this.isCompleted = false;
    }
    
    async handleChatSubmit(event) {
        // 사용자 메시지 처리
        // API 호출 및 응답 처리  
        // UI 업데이트
    }
    
    updateUnderstandingGauge(score) {
        // 이해도 게이지 실시간 업데이트
        // 단계별 피드백 메시지 표시
    }
}
```

### 3. CSS 아키텍처

#### **세그먼트 컨트롤 시스템:**
```css
.segment-control {
    display: flex;
    background: #F1F5F9;
    border-radius: 12px;
    padding: 4px;
    gap: 2px;
}

.segment-option {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px 12px;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.segment-control input[type="radio"]:checked + .segment-option {
    background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
    transform: translateY(-1px);
}
```

---

## 🔧 핵심 기술 구현

### 1. 듀얼 AI 병렬 처리

```python
async def socratic_chat(request: SocraticChatRequest):
    """소크라테스식 대화 및 이해도 평가"""
    try:
        socratic_service = get_socratic_service()
        assessment_service = get_assessment_service()
        
        # 병렬로 산파법 응답과 이해도 평가 실행
        socratic_response = await socratic_service.generate_socratic_response(
            request.topic, 
            request.messages, 
            request.understanding_level,
            request.difficulty
        )
        
        # 사용자의 마지막 메시지와 AI 응답으로 이해도 평가 
        last_user_message = request.messages[-1]["content"] if request.messages else ""
        understanding_score = await assessment_service.evaluate_understanding(
            request.topic, 
            last_user_message, 
            socratic_response,
            request.understanding_level,
            request.difficulty,
            request.messages  # 전체 대화 기록 전달
        )
        
        is_completed = understanding_score >= 100
        
        return SocraticChatResponse(
            socratic_response=socratic_response,
            understanding_score=understanding_score,
            is_completed=is_completed
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 점수 조정 알고리즘

```python  
def apply_score_adjustment(self, ai_suggested_score: int, current_level: int, difficulty: str) -> int:
    """난이도별 점수 변동 제한 적용"""
    setting = self.difficulty_settings.get(difficulty, self.difficulty_settings["normal"])
    
    # 변동 제한 계산
    max_increase = int(setting['max_increase'] * 100)
    max_decrease = int(setting['max_decrease'] * 100)
    
    max_allowed = current_level + max_increase
    min_allowed = max(0, current_level - max_decrease)
    
    # 점수 조정기 적용
    final_score = max(min_allowed, min(max_allowed, ai_suggested_score))
    final_score = max(0, min(100, final_score))  # 0-100 범위 제한
    
    return final_score
```

### 3. 반응형 UI 시스템

```css
/* 데스크톱: 가로 배치 */
.segment-control {
    flex-direction: row;
}

.segment-option {
    flex-direction: column;
    min-height: 80px;
}

/* 모바일: 세로 배치 */
@media (max-width: 768px) {
    .segment-control {
        flex-direction: column;
        gap: 4px;
    }
    
    .segment-option {
        flex-direction: row;
        min-height: 60px;
        text-align: left;
    }
    
    .segment-icon {
        margin-right: 12px;
        margin-bottom: 0;
    }
}
```

---

## 📊 성능 및 최적화

### 1. 응답 속도 최적화
- **비동기 처리**: 듀얼 AI 병렬 실행으로 응답 시간 단축
- **모델 선택**: GPT-4o-mini로 속도와 품질 균형
- **토큰 최적화**: 프롬프트 길이 최적화로 비용 절감

### 2. 사용자 경험 최적화
- **로딩 상태**: 각 단계별 명확한 로딩 인디케이터
- **오류 처리**: 사용자 친화적 오류 메시지
- **상태 관리**: 브라우저 새로고침 시에도 설정 유지

### 3. 확장성 설계
- **모듈형 구조**: 각 서비스의 독립적 확장 가능
- **API 기반**: 다양한 클라이언트 지원 가능  
- **설정 기반**: 난이도 및 평가 기준 동적 조정

---

## 🔒 보안 및 안정성

### 1. API 보안
- **환경 변수**: OpenAI API 키 등 민감 정보 분리
- **입력 검증**: 사용자 입력에 대한 서버사이드 검증
- **에러 핸들링**: 예외 상황 안전 처리

### 2. 콘텐츠 안전성
- **주제 필터링**: 교육적으로 부적절한 주제 차단
- **연령 적합성**: 중학생 수준에 맞는 콘텐츠 보장
- **교육적 가치**: 모든 응답의 교육적 목적 부합

---

## 🚀 배포 및 운영

### 1. 로컬 개발 환경

```bash
# 백엔드 실행
cd backend
pip install -r requirements.txt
python main.py

# 프론트엔드 접속  
http://localhost:8000
```

### 2. 환경 변수 설정

```bash
# .env 파일
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### 3. 의존성 관리

```txt
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-dotenv==1.0.0
openai==1.3.7
pydantic==2.5.0
httpx==0.25.2
```

---

## 🔮 향후 개발 계획

### 1. 기능 확장
- **PDF 파일 지원**: 문서 기반 학습
- **웹 링크 분석**: 뉴스 기사 등 외부 콘텐츠
- **음성 인터페이스**: 음성 입력/출력 지원
- **협업 기능**: 학생 간 질문 공유

### 2. 기술 개선  
- **캐싱 시스템**: Redis 활용한 응답 캐싱
- **데이터베이스**: 학습 이력 영구 저장
- **실시간 통신**: WebSocket 기반 채팅
- **모니터링**: 학습 분석 대시보드

### 3. 교육적 발전
- **개인화 AI**: 학습 스타일별 맞춤 튜터
- **교사 도구**: 학생 진도 관리 기능
- **평가 고도화**: 더 정교한 이해도 측정
- **다국어 지원**: 글로벌 서비스 확장

---

## 📝 결론

LLM Classroom Proto4는 최신 AI 기술과 2500년 전 소크라테스의 교육 철학을 융합한 혁신적인 교육 플랫폼입니다. **듀얼 AI 시스템**, **적응형 학습**, **직관적 UI/UX**를 통해 학생들의 진정한 학습을 지원합니다.

특히 **점수에 매몰되지 않는 학습 환경**과 **개인맞춤형 난이도 조정**을 통해, 모든 학습자가 자신만의 속도로 깊이 있는 탐구를 할 수 있도록 설계되었습니다.

---

*버전: 1.0.0*  
*최종 업데이트: 2025년 1월 29일*  
*개발팀: LLM Classroom Proto4 Team*