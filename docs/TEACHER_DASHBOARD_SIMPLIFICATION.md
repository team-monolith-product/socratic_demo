# 📋 소크라테스 아카데미 교사 대시보드 간소화 기획서 (✅ 완료됨)

## 🎯 개요

교사용 인터페이스를 학생용과 유사한 단순한 플로우로 재설계하여 사용성을 향상시키고, 한 번에 하나의 세션만 관리하는 직관적인 구조로 변경합니다.

**✅ 구현 완료**: 2024년 완료, 기존 복잡한 teacher 서비스를 제거하고 teacher-simplified로 대체하였습니다.

---

## 🔄 변경 사항 요약

### ✅ 유지되는 기능
- **세션 설정하기**: 주제, 난이도, 점수 표시 옵션 설정
- **접속 정보 제공**: QR 코드, 직접 링크
- **실시간 대시보드**: 학생 진행 상황 실시간 모니터링 테이블

### ❌ 제거되는 기능
- **세션 관리 목록**: 여러 세션을 나열하는 대시보드 뷰
- **세션 삭제 기능**: 개별 세션 삭제 옵션
- **세션 종료 기능**: 명시적인 세션 종료 버튼

### 🆕 새로운 기능
- **단일 세션 중심 UI**: 한 번에 하나의 세션만 관리
- **로컬스토리지 기반 세션 복원**: 새로고침 시 현재 세션 자동 복원
- **세션 초기화 확인**: 새 세션 시작 시 기존 세션 덮어쓰기 경고

---

## 📱 새로운 사용자 플로우

### 1️⃣ **초기 진입 화면**
```
페이지 접속 → 학생용과 유사한 세션 설정 화면 직접 표시
```

**화면 구성:**
- **헤더**: 브랜드 로고 + 제목
- **메인 영역**: 세션 설정 폼 (현재 모달 내용과 동일)
  - 세션 제목 입력
  - 학습 주제 입력
  - 난이도 선택 (쉬움/보통/어려움)
  - 점수 표시 설정 (표시/숨김)
- **액션 버튼**: "세션 시작하기"

### 2️⃣ **세션 생성 및 QR 표시**
```
세션 설정 완료 → 대시보드 이동 + QR 모달 자동 표시
```

**플로우:**
1. "세션 시작하기" 버튼 클릭
2. 백엔드에서 세션 생성
3. 세션 ID를 로컬스토리지에 저장
4. 대시보드 화면으로 자동 이동
5. QR 코드 모달 자동 팝업

### 3️⃣ **세션 대시보드**
```
QR 모달 닫기 → 실시간 학생 모니터링 대시보드
```

**화면 구성:**
- **헤더**:
  - 세션 제목 + 마지막 업데이트 시간
  - QR 코드 보기 버튼
  - 새로고침 버튼
  - 새 세션 시작하기 버튼
- **메인 영역**:
  - 세션 정보 카드 (참여 학생 수, 진행 시간, 평균 점수, 총 메시지)
  - 학생 진행 상황 실시간 테이블

### 4️⃣ **새 세션 시작**
```
새 세션 시작하기 버튼 클릭 → 확인 모달 → 세션 설정 화면
```

**확인 모달 내용:**
- "새 세션을 시작하면 현재 진행 중인 세션이 종료됩니다."
- "계속하시겠습니까?"
- [취소] / [새 세션 시작]

---

## 🏗️ 화면별 상세 설계

### 📄 **1. 초기 세션 설정 화면**

**위치**: `/pages/teacher.html` 메인 뷰
**조건**: 로컬스토리지에 활성 세션이 없는 경우

```html
<div class="session-setup-main">
  <header class="simple-header">
    <div class="brand">소크라테스 아카데미 - 교사용</div>
  </header>

  <main class="setup-content">
    <h1>새로운 학습 세션을 시작해보세요</h1>
    <form class="session-form">
      <!-- 기존 모달 내용과 동일 -->
      <div class="form-group">
        <label>세션 제목</label>
        <input type="text" placeholder="예: 기후변화 토론">
      </div>

      <div class="form-group">
        <label>학습 주제</label>
        <textarea placeholder="학습 목표와 토론 주제를 입력하세요"></textarea>
      </div>

      <div class="difficulty-section">
        <!-- 난이도 선택 -->
      </div>

      <div class="score-section">
        <!-- 점수 표시 설정 -->
      </div>

      <button type="submit" class="start-session-btn">
        세션 시작하기
      </button>
    </form>
  </main>
</div>
```

### 📊 **2. 세션 대시보드 화면**

**위치**: `/pages/teacher.html` 대시보드 뷰
**조건**: 로컬스토리지에 활성 세션이 있는 경우

```html
<div class="session-dashboard">
  <header class="dashboard-header">
    <div class="session-info">
      <h1 id="sessionTitle">세션 제목</h1>
      <div class="last-update">마지막 업데이트: 14:30:25</div>
    </div>

    <div class="header-actions">
      <button id="showQRBtn" class="action-btn secondary">
        📱 QR 코드 보기
      </button>
      <button id="refreshBtn" class="action-btn secondary">
        🔄 새로고침
      </button>
      <button id="newSessionBtn" class="action-btn primary">
        ✨ 새 세션 시작
      </button>
    </div>
  </header>

  <main class="dashboard-content">
    <!-- 기존 세션 정보 카드들 -->
    <div class="session-stats">
      <!-- 참여 학생, 진행 시간, 평균 점수, 총 메시지 -->
    </div>

    <!-- 기존 학생 테이블 -->
    <div class="students-section">
      <!-- 학생 진행 상황 테이블 -->
    </div>
  </main>
</div>
```

### 🔔 **3. 새 세션 시작 확인 모달**

```html
<div id="confirmNewSessionModal" class="modal">
  <div class="modal-content">
    <div class="modal-header">
      <h3>⚠️ 새 세션 시작</h3>
    </div>
    <div class="modal-body">
      <p>새 세션을 시작하면 현재 진행 중인 세션이 종료됩니다.</p>
      <p>학생들의 진행 상황은 저장되지만, 새로운 학생들만 참여할 수 있게 됩니다.</p>
      <p><strong>계속하시겠습니까?</strong></p>
    </div>
    <div class="modal-actions">
      <button class="secondary-button">취소</button>
      <button class="primary-button" id="confirmNewSession">새 세션 시작</button>
    </div>
  </div>
</div>
```

---

## 💾 데이터 관리 전략

### 🗄️ **로컬스토리지 구조**

```javascript
// 현재 활성 세션 정보
const activeSession = {
  sessionId: "sess_abc123",
  title: "기후변화 토론",
  topic: "기후변화의 원인과 해결책...",
  difficulty: "normal",
  showScore: true,
  createdAt: "2024-01-15T10:30:00Z",
  lastAccessedAt: "2024-01-15T14:30:00Z"
}

localStorage.setItem('activeSession', JSON.stringify(activeSession));
```

### 🔄 **세션 복원 로직**

```javascript
class SessionManager {
  // 페이지 로드 시 실행
  async initializeSession() {
    const savedSession = this.getSavedSession();

    if (savedSession) {
      // 세션이 여전히 유효한지 백엔드에서 확인
      const isValid = await this.validateSession(savedSession.sessionId);

      if (isValid) {
        // 대시보드 표시
        this.showDashboard(savedSession);
      } else {
        // 만료된 세션 정리 후 설정 화면 표시
        this.clearSavedSession();
        this.showSetupScreen();
      }
    } else {
      // 새 세션 설정 화면 표시
      this.showSetupScreen();
    }
  }

  // 세션 저장
  saveSession(sessionData) {
    const sessionInfo = {
      ...sessionData,
      lastAccessedAt: new Date().toISOString()
    };
    localStorage.setItem('activeSession', JSON.stringify(sessionInfo));
  }

  // 세션 정리
  clearSavedSession() {
    localStorage.removeItem('activeSession');
  }
}
```

### 🏗️ **백엔드 데이터 구조 (유지)**

- 기존 데이터베이스 구조 그대로 유지
- 모든 세션과 학생 데이터는 DB에 저장
- 로컬스토리지는 UI 편의성을 위한 캐시 용도로만 사용

---

## 🎨 UI/UX 가이드라인

### 🎯 **설계 원칙**
1. **단순성**: 한 번에 하나의 주요 작업만 집중
2. **명확성**: 현재 상태와 다음 액션이 명확히 보임
3. **일관성**: 학생용 UI와 유사한 디자인 패턴 사용

### 🎨 **비주얼 디자인**

**색상 체계:**
- Primary: 기존 파란색 계열 유지
- Secondary: 회색 계열 (새로고침, QR 버튼)
- Warning: 주황색 (새 세션 시작 경고)
- Success: 초록색 (완료 상태)

**레이아웃:**
- **모바일 우선**: 반응형 디자인
- **카드 기반**: 정보 구조화를 위한 카드 레이아웃
- **여백 활용**: 충분한 여백으로 가독성 향상

### 📱 **반응형 디자인**

```css
/* 모바일 (768px 미만) */
- 세션 설정 폼: 단일 컬럼
- 헤더 액션: 세로 스택
- 테이블: 가로 스크롤

/* 태블릿 (768px-1024px) */
- 세션 설정 폼: 2컬럼 그리드
- 헤더 액션: 가로 배치
- 테이블: 일부 컬럼 숨김

/* 데스크톱 (1024px 이상) */
- 세션 설정 폼: 최적화된 2컬럼
- 헤더 액션: 오른쪽 정렬
- 테이블: 모든 컬럼 표시
```

---

## ⚙️ 기술적 구현 사항

### 🔧 **JavaScript 모듈 구조**

```javascript
// teacher-simplified.js
class SimplifiedTeacherDashboard {
  constructor() {
    this.sessionManager = new SessionManager();
    this.currentSession = null;
    this.autoRefreshInterval = null;
  }

  // 메인 초기화
  async init() {
    await this.sessionManager.initializeSession();
    this.setupEventListeners();
  }

  // 화면 전환
  showSetupScreen() {
    // 세션 설정 화면 표시
  }

  showDashboard(sessionData) {
    // 대시보드 화면 표시
    // 자동 새로고침 시작
  }

  // 이벤트 핸들러
  handleSessionCreate(formData) {
    // 세션 생성 → QR 모달 → 대시보드
  }

  handleNewSessionStart() {
    // 확인 모달 → 기존 세션 정리 → 설정 화면
  }
}
```

### 🌐 **API 엔드포인트 변경사항**

**기존 API 유지하되 추가:**

```javascript
// 세션 유효성 검증
GET /api/sessions/{sessionId}/validate
Response: { valid: boolean, session: SessionData }

// 활성 세션 정리 (소프트 종료)
POST /api/sessions/{sessionId}/archive
Response: { success: boolean }
```

### 📦 **파일 구조 변경**

```
frontend/
├── pages/
│   ├── teacher.html (메인 화면 - 단순화)
│   └── student-session.html (기존 유지)
├── static/
│   ├── css/
│   │   ├── teacher-simplified.css (새로 생성)
│   │   └── teacher.css (기존 - 점진적 제거)
│   └── js/
│       ├── teacher-simplified.js (새로 생성)
│       └── teacher-dashboard.js (기존 - 점진적 제거)
```

---

## 🧪 테스트 시나리오

### ✅ **기본 플로우 테스트**

1. **신규 사용자 플로우**
   - [ ] 페이지 첫 접속 시 세션 설정 화면 표시
   - [ ] 세션 생성 후 QR 모달 자동 표시
   - [ ] QR 모달 닫기 후 대시보드 정상 표시

2. **기존 사용자 플로우**
   - [ ] 새로고침 시 기존 세션 자동 복원
   - [ ] 만료된 세션일 경우 설정 화면으로 이동

3. **세션 관리 플로우**
   - [ ] 새 세션 시작 시 확인 모달 표시
   - [ ] 확인 후 기존 세션 정리 및 새 설정 화면 표시

### 🔄 **에지 케이스 테스트**

1. **네트워크 오류**
   - [ ] 세션 생성 실패 시 에러 메시지 표시
   - [ ] 네트워크 복구 시 자동 재시도

2. **브라우저 호환성**
   - [ ] 로컬스토리지 미지원 브라우저 대응
   - [ ] 쿠키 비활성화 상태 대응

3. **동시 접속**
   - [ ] 여러 브라우저 탭에서 동일 세션 접근 시 동기화

---

## 📈 마이그레이션 계획

### 🎯 **1단계: 새 UI 개발 (1-2주)**
- 새로운 단순화된 UI 컴포넌트 개발
- 로컬스토리지 기반 세션 관리 로직 구현
- 기존 API와 연동

### 🔄 **2단계: 병렬 운영 (1주)**
- 기존 UI와 새 UI 병렬 제공
- 사용자 피드백 수집
- 버그 수정 및 개선

### 🚀 **3단계: 전환 완료 (1주)**
- 새 UI를 기본으로 설정
- 기존 UI 코드 제거
- 성능 최적화

### 📋 **롤백 계획**
- 기존 UI 코드는 1개월간 보관
- 문제 발생 시 즉시 롤백 가능
- 사용자 데이터는 기존 구조 유지로 영향 없음

---

## 📊 성공 지표

### 📈 **정량적 지표**
- **세션 생성 시간**: 기존 대비 50% 단축 목표
- **사용자 이탈률**: 설정 단계에서 20% 이하 유지
- **페이지 로드 시간**: 2초 이내

### 📝 **정성적 지표**
- **사용 편의성**: 교사 피드백을 통한 만족도 조사
- **학습 곡선**: 신규 사용자의 첫 세션 생성까지 소요 시간
- **에러 발생률**: 세션 관리 관련 오류 최소화

---

이 기획서에 따라 구현하면 교사들이 더 직관적이고 간단하게 소크라테스 아카데미를 사용할 수 있게 됩니다. 복잡한 세션 관리 기능을 제거하고 핵심 기능에 집중함으로써 사용성을 크게 개선할 수 있을 것입니다.