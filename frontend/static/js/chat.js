class SocraticChatHandler {
    constructor() {
        this.apiBase = this.getApiBase();
        this.topic = '';
        this.messages = [];
        this.understandingScore = 0;
        this.isCompleted = false;
        this.showScore = true; // 점수 표시 여부
        this.difficulty = 'normal'; // 학습 난이도
        
        this.init();
    }
    
    getApiBase() {
        if (typeof window !== 'undefined' && window.__API_BASE__) {
            return window.__API_BASE__;
        }
        return '/api/v1';
    }

    init() {
        // URL에서 주제, 난이도, 점수 표시 옵션 추출
        const urlParams = this.getUrlParams();
        this.topic = urlParams.topic;
        this.difficulty = urlParams.difficulty || 'normal';
        this.showScore = urlParams.showScore === 'true';
        this.mode = urlParams.mode || 'teacher';
        this.sessionId = urlParams.session_id || '';
        this.studentName = urlParams.student_name || '';
        
        if (!this.topic) {
            alert('주제가 설정되지 않았습니다.');
            window.location.href = '/';
            return;
        }
        
        // UI 초기화
        this.initializeUI();
        
        // 이벤트 리스너 설정
        this.setupEventListeners();
        
        // 첫 메시지 로드
        this.loadInitialMessage();
    }
    
    getUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        return {
            topic: decodeURIComponent(urlParams.get('topic') || ''),
            difficulty: urlParams.get('difficulty') || 'normal',
            showScore: urlParams.get('showScore') || 'true',
            mode: urlParams.get('mode') || 'teacher',
            session_id: urlParams.get('session_id') || '',
            student_name: decodeURIComponent(urlParams.get('student_name') || '')
        };
    }
    
    initializeUI() {
        // 주제 타이틀 설정
        const topicTitle = document.getElementById('topicTitle');
        if (topicTitle) {
            topicTitle.textContent = this.topic;
        }

        // 학생 모드일 때 주제 변경 버튼 숨기기
        if (this.mode === 'student') {
            const backBtn = document.getElementById('backBtn');
            if (backBtn) {
                backBtn.style.display = 'none';
            }
        }

        // 점수 표시 옵션에 따라 UI 조정
        const progressSection = document.querySelector('.progress-section');
        const chatContainer = document.querySelector('.chat-container');
        
        if (progressSection) {
            if (this.showScore) {
                progressSection.style.display = 'block';
                // 이해도 게이지 초기화
                this.updateUnderstandingGauge(0);
                // score-hidden 클래스 제거
                if (chatContainer) {
                    chatContainer.classList.remove('score-hidden');
                }
            } else {
                // 점수 숨김 모드
                if (chatContainer) {
                    chatContainer.classList.add('score-hidden');
                }
                // 모바일에서는 CSS로 숨김 처리, 데스크톱에서는 display none
                if (window.innerWidth > 768) {
                    progressSection.style.display = 'none';
                    // 채팅 영역을 전체 너비로 확장
                    const chatMain = document.querySelector('.chat-main');
                    if (chatMain) {
                        chatMain.style.gridTemplateColumns = '1fr';
                    }
                }
            }
        }
    }
    
    setupEventListeners() {
        // 폼 제출 이벤트 통합 처리
        this.setupFormHandlers();
        
        // 버튼 이벤트 처리
        this.setupButtonHandlers();
        
        // 키보드 이벤트 통합 처리
        this.setupKeyboardHandlers();
        
        // 모바일 기능 초기화
        this.setupMobileFeatures();
    }
    
    setupFormHandlers() {
        const forms = ['chatForm', 'chatFormMobile'];
        forms.forEach(formId => {
            const form = document.getElementById(formId);
            if (form) {
                form.addEventListener('submit', (e) => this.handleChatSubmit(e));
            }
        });
    }
    
    setupButtonHandlers() {
        // 모바일 전송 버튼
        const sendBtnMobile = document.getElementById('sendBtnMobile');
        if (sendBtnMobile) {
            sendBtnMobile.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleChatSubmit(e);
            });
        }
        
        // 뒤로가기 버튼
        const backBtn = document.getElementById('backBtn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                window.location.href = '/';
            });
        }
    }
    
    setupKeyboardHandlers() {
        const inputs = [
            { inputId: 'messageInput', formId: 'chatForm' },
            { inputId: 'messageInputMobile', formId: 'chatFormMobile' }
        ];
        
        inputs.forEach(({ inputId, formId }) => {
            const input = document.getElementById(inputId);
            const form = document.getElementById(formId);
            
            if (input && form) {
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        form.dispatchEvent(new Event('submit'));
                    }
                });
            }
        });
    }
    
    setupMobileFeatures() {
        // 모바일 환경에서만 실행
        if (window.innerWidth <= 768) {
            this.initializeDrawer();
        }
        
        // 윈도우 리사이즈 이벤트
        window.addEventListener('resize', () => {
            if (window.innerWidth <= 768) {
                this.initializeDrawer();
            }
        });
    }
    
    initializeDrawer() {
        const scoreDrawer = document.getElementById('scoreDrawer');
        const drawerHandleArea = document.getElementById('drawerHandleArea');
        
        if (!scoreDrawer) return;
        
        // 이미 초기화되었는지 확인
        if (drawerHandleArea && !drawerHandleArea.hasAttribute('data-initialized')) {
            drawerHandleArea.setAttribute('data-initialized', 'true');
            
            // 드로어 핸들 영역 클릭으로 열기/닫기
            drawerHandleArea.addEventListener('click', (e) => {
                e.stopPropagation(); // 이벤트 버블링 중지
                this.toggleDrawer();
            });
            
            // 드로어 외부 클릭시 닫기
            document.addEventListener('click', (e) => {
                if (scoreDrawer.classList.contains('open') && 
                    !scoreDrawer.contains(e.target)) {
                    // 채팅 영역 클릭시에만 닫기
                    if (e.target.closest('.chat-section')) {
                        this.closeDrawer();
                    }
                }
            });
        }
    }
    
    openDrawer() {
        const scoreDrawer = document.getElementById('scoreDrawer');
        if (scoreDrawer && !this.isScoreHidden()) {
            scoreDrawer.classList.add('open');
        }
    }
    
    closeDrawer() {
        const scoreDrawer = document.getElementById('scoreDrawer');
        if (scoreDrawer) {
            scoreDrawer.classList.remove('open');
        }
    }
    
    toggleDrawer() {
        const scoreDrawer = document.getElementById('scoreDrawer');
        if (scoreDrawer && !this.isScoreHidden()) {
            if (scoreDrawer.classList.contains('open')) {
                this.closeDrawer();
            } else {
                this.openDrawer();
            }
        }
    }
    
    isScoreHidden() {
        return !this.showScore;
    }
    
    // 현재 활성 영역 확인 (모바일 드로어 방식)
    getCurrentActiveSection() {
        if (window.innerWidth <= 768) {
            const scoreDrawer = document.getElementById('scoreDrawer');
            if (scoreDrawer && scoreDrawer.classList.contains('open')) {
                return 'progress';
            }
            return 'chat';
        }
        return 'both'; // 데스크톱에서는 둘 다 보임
    }
    
    // 점수 업데이트 알림 효과
    triggerGlowEffect(targetSection) {
        // 점수 숨김 모드에서는 알림 효과 없음
        if (this.isScoreHidden()) return;
        
        if (window.innerWidth <= 768) {
            const currentActive = this.getCurrentActiveSection();
            
            // 진행률 업데이트 시 드로어가 닫혀있으면 알림 효과만
            if (targetSection === 'progress' && currentActive === 'chat') {
                this.showScoreUpdateNotification();
            }
        }
    }
    
    // 점수 업데이트 알림 애니메이션
    showScoreUpdateNotification() {
        const scoreDrawer = document.getElementById('scoreDrawer');
        const drawerHandleArea = document.getElementById('drawerHandleArea');
        
        if (scoreDrawer && drawerHandleArea) {
            // 드로어 흔들기 애니메이션
            scoreDrawer.classList.add('score-updated');
            
            // 핸들 글로우 효과
            drawerHandleArea.classList.add('glow');
            
            // 1초 후 효과 제거 (절반으로 단축)
            setTimeout(() => {
                scoreDrawer.classList.remove('score-updated');
                drawerHandleArea.classList.remove('glow');
            }, 1000);
        }
    }
    
    // 글로우 효과는 드로어 방식에서는 자동 열기로 대체
    
    async loadInitialMessage() {
        try {
            const response = await fetch(`${this.apiBase}/chat/initial`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    topic: this.topic,
                    difficulty: this.difficulty
                })
            });
            
            if (!response.ok) {
                throw new Error('초기 메시지 로드에 실패했습니다.');
            }
            
            const data = await response.json();
            
            // 로딩 메시지 제거
            this.hideLoadingMessage();
            
            // AI 첫 메시지 표시
            this.addMessage('ai', data.initial_message);
            
            // 입력 필드 활성화
            this.enableInput();
            
        } catch (error) {
            console.error('Error loading initial message:', error);
            this.hideLoadingMessage();
            this.addMessage('ai', '안녕하세요! 함께 탐구해볼까요?');
            this.enableInput();
        }
    }
    
    async handleChatSubmit(event) {
        event.preventDefault();
        
        // 모바일과 데스크톱 입력창 모두 확인
        const messageInput = document.getElementById('messageInput');
        const messageInputMobile = document.getElementById('messageInputMobile');
        
        let currentInput = null;
        let userMessage = '';
        
        // 모바일 입력창 우선 확인 (모바일에서는 데스크톱 입력창이 숨겨짐)
        if (messageInputMobile && window.innerWidth <= 768) {
            currentInput = messageInputMobile;
            userMessage = messageInputMobile.value.trim();
        } else if (messageInput && window.innerWidth > 768) {
            currentInput = messageInput;
            userMessage = messageInput.value.trim();
        }
        
        if (!userMessage || !currentInput) {
            return;
        }
        
        // 사용자 메시지 추가
        this.addMessage('user', userMessage);
        this.messages.push({ role: 'user', content: userMessage });
        
        // 입력 필드 초기화 및 비활성화
        currentInput.value = '';
        this.disableInput();
        
        try {
            // AI 응답 요청
            const response = await fetch(`${this.apiBase}/chat/socratic`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    topic: this.topic,
                    messages: this.messages,
                    understanding_level: this.understandingScore,
                    difficulty: this.difficulty
                })
            });
            
            if (!response.ok) {
                throw new Error('AI 응답을 받아올 수 없습니다.');
            }
            
            const data = await response.json();
            
            // AI 응답 추가
            this.addMessage('ai', data.socratic_response);
            this.messages.push({ role: 'assistant', content: data.socratic_response });
            
            // 점수 표시가 활성화된 경우에만 이해도 업데이트
            if (this.showScore) {
                this.updateSocraticEvaluation(data);
                
                // 완료 체크
                if (data.is_completed && !this.isCompleted) {
                    this.showCompletionCelebration();
                    this.isCompleted = true;
                }
            } else {
                // 점수 숨김 모드에서는 내부적으로만 점수 추적
                this.understandingScore = data.understanding_score;
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('ai', '죄송해요, 일시적인 오류가 발생했습니다. 다시 말씀해 주세요.');
        } finally {
            // 입력 필드 다시 활성화
            this.enableInput();
        }
    }
    
    addMessage(role, content) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'ai' ? '🏛️' : '👤';
        
        // AI 메시지일 때 채팅 영역에 글로우 효과 트리거
        if (role === 'ai') {
            this.triggerGlowEffect('chat');
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        messagesContainer.appendChild(messageDiv);
        
        // 스크롤을 맨 아래로
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    updateSocraticEvaluation(data) {
        this.understandingScore = data.understanding_score;
        
        // 기존 게이지 업데이트
        this.updateUnderstandingGauge(data.understanding_score);
        
        // 5차원 평가 결과 시각화
        if (data.dimensions) {
            this.updateDimensionVisualization(data.dimensions);
        }
        
        // 성장 지표 및 피드백 업데이트
        if (data.growth_indicators) {
            this.updateGrowthIndicators(data.growth_indicators);
        }
        
        if (data.next_focus) {
            this.updateNextFocus(data.next_focus);
        }
        
        // 진행률 업데이트 시 진행률 영역에 글로우 효과 트리거
        this.triggerGlowEffect('progress');
    }

    updateUnderstandingGauge(score) {
        this.understandingScore = score;
        
        const gaugeFill = document.getElementById('gaugeFill');
        const scoreText = document.getElementById('scoreText');
        const progressFeedback = document.getElementById('progressFeedback');
        
        if (gaugeFill) {
            gaugeFill.style.width = `${score}%`;
        }
        
        if (scoreText) {
            scoreText.textContent = score;
        }
        
        if (progressFeedback) {
            progressFeedback.textContent = this.getProgressFeedback(score);
        }
    }
    
    updateDimensionVisualization(dimensions) {
        // 5차원 레이더 차트 또는 바 차트로 시각화
        const dimensionNames = {
            depth: '🌊 사고 깊이',
            breadth: '🌐 사고 확장', 
            application: '🔗 실생활 적용',
            metacognition: '🪞 메타인지',
            engagement: '⚡ 소크라테스적 참여'
        };
        
        // 기존 차원 정보가 있다면 업데이트
        let dimensionContainer = document.getElementById('dimensionContainer');
        if (!dimensionContainer) {
            // 컨테이너가 없다면 생성
            dimensionContainer = this.createDimensionContainer();
        }
        
        // 각 차원별 점수 표시
        Object.entries(dimensions).forEach(([key, value]) => {
            const dimensionElement = document.getElementById(`dimension-${key}`);
            if (dimensionElement) {
                const bar = dimensionElement.querySelector('.dimension-bar-fill');
                const scoreText = dimensionElement.querySelector('.dimension-score');
                
                if (bar) bar.style.width = `${value}%`;
                if (scoreText) scoreText.textContent = value;
                
                // 색상 변경 (점수에 따라)
                if (bar) {
                    bar.className = `dimension-bar-fill ${this.getScoreClass(value)}`;
                }
            }
        });
    }
    
    createDimensionContainer() {
        const drawerContent = document.querySelector('.drawer-content');
        if (!drawerContent) return null;
        
        const dimensionContainer = document.createElement('div');
        dimensionContainer.id = 'dimensionContainer';
        dimensionContainer.className = 'dimension-container';
        dimensionContainer.innerHTML = `
            <h4>📊 소크라테스식 5차원 평가</h4>
            <div class="dimensions-grid">
                <div id="dimension-depth" class="dimension-item">
                    <span class="dimension-label">🌊 사고 깊이</span>
                    <div class="dimension-bar">
                        <div class="dimension-bar-fill" style="width: 0%"></div>
                    </div>
                    <span class="dimension-score">0</span>
                </div>
                <div id="dimension-breadth" class="dimension-item">
                    <span class="dimension-label">🌐 사고 확장</span>
                    <div class="dimension-bar">
                        <div class="dimension-bar-fill" style="width: 0%"></div>
                    </div>
                    <span class="dimension-score">0</span>
                </div>
                <div id="dimension-application" class="dimension-item">
                    <span class="dimension-label">🔗 실생활 적용</span>
                    <div class="dimension-bar">
                        <div class="dimension-bar-fill" style="width: 0%"></div>
                    </div>
                    <span class="dimension-score">0</span>
                </div>
                <div id="dimension-metacognition" class="dimension-item">
                    <span class="dimension-label">🪞 메타인지</span>
                    <div class="dimension-bar">
                        <div class="dimension-bar-fill" style="width: 0%"></div>
                    </div>
                    <span class="dimension-score">0</span>
                </div>
                <div id="dimension-engagement" class="dimension-item">
                    <span class="dimension-label">⚡ 소크라테스적 참여</span>
                    <div class="dimension-bar">
                        <div class="dimension-bar-fill" style="width: 0%"></div>
                    </div>
                    <span class="dimension-score">0</span>
                </div>
            </div>
        `;
        
        // 기존 이해도 게이지 다음에 삽입
        const understandingGauge = drawerContent.querySelector('.understanding-gauge');
        if (understandingGauge) {
            understandingGauge.insertAdjacentElement('afterend', dimensionContainer);
        } else {
            drawerContent.appendChild(dimensionContainer);
        }
        
        return dimensionContainer;
    }
    
    updateGrowthIndicators(indicators) {
        let growthContainer = document.getElementById('growthContainer');
        if (!growthContainer) {
            growthContainer = this.createGrowthContainer();
        }
        
        const indicatorsList = growthContainer.querySelector('.growth-list');
        if (indicatorsList && indicators.length > 0) {
            indicatorsList.innerHTML = indicators.map(indicator => 
                `<li class="growth-item">🌱 ${indicator}</li>`
            ).join('');
        }
    }
    
    createGrowthContainer() {
        const drawerContent = document.querySelector('.drawer-content');
        if (!drawerContent) return null;
        
        const growthContainer = document.createElement('div');
        growthContainer.id = 'growthContainer';
        growthContainer.className = 'growth-container';
        growthContainer.innerHTML = `
            <h4>📈 성장 지표</h4>
            <ul class="growth-list"></ul>
        `;
        
        // 이해도 게이지 다음에 삽입 (대화 팁 전에)
        const understandingGauge = drawerContent.querySelector('.understanding-gauge');
        if (understandingGauge) {
            understandingGauge.insertAdjacentElement('afterend', growthContainer);
        } else {
            drawerContent.appendChild(growthContainer);
        }
        
        return growthContainer;
    }
    
    updateNextFocus(focus) {
        let focusContainer = document.getElementById('focusContainer');
        if (!focusContainer) {
            focusContainer = this.createFocusContainer();
        }
        
        const focusText = focusContainer.querySelector('.focus-text');
        if (focusText) {
            focusText.textContent = focus;
        }
    }
    
    createFocusContainer() {
        const drawerContent = document.querySelector('.drawer-content');
        if (!drawerContent) return null;
        
        const focusContainer = document.createElement('div');
        focusContainer.id = 'focusContainer';
        focusContainer.className = 'focus-container';
        focusContainer.innerHTML = `
            <h4>🎯 다음 탐구 방향</h4>
            <p class="focus-text"></p>
        `;
        
        // 성장 지표 다음에 삽입 (대화 팁 전에)
        const growthContainer = drawerContent.querySelector('.growth-container');
        if (growthContainer) {
            growthContainer.insertAdjacentElement('afterend', focusContainer);
        } else {
            // 성장 지표가 없으면 이해도 게이지 다음에
            const understandingGauge = drawerContent.querySelector('.understanding-gauge');
            if (understandingGauge) {
                understandingGauge.insertAdjacentElement('afterend', focusContainer);
            } else {
                drawerContent.appendChild(focusContainer);
            }
        }
        
        return focusContainer;
    }
    
    getScoreClass(score) {
        if (score >= 80) return 'score-excellent';
        if (score >= 60) return 'score-good';
        if (score >= 40) return 'score-fair';
        return 'score-needs-improvement';
    }
    
    getProgressFeedback(score) {
        if (score <= 20) {
            return "탐구 시작: 이제 막 탐구를 시작했어요! 함께 알아가봐요 🌱";
        } else if (score <= 40) {
            return "기초 이해: 기본적인 이해가 생겼어요! 더 깊이 들어가볼까요? 💡";
        } else if (score <= 60) {
            return "초급 수준: 개념을 잘 이해하고 있어요! 연결고리를 찾아보세요 🔗";
        } else if (score <= 80) {
            return "중급 수준: 훌륭한 이해력이에요! 비판적 사고를 시작해보세요 🧠";
        } else if (score < 100) {
            return "고급 수준: 전문가 수준의 깊은 이해를 보여주고 있어요! 🌟";
        } else {
            return "마스터 완성: 완벽한 이해를 달성했습니다! 🏆";
        }
    }
    
    showCompletionCelebration() {
        const celebration = document.getElementById('completionCelebration');
        if (celebration) {
            celebration.style.display = 'block';
            
            // 3초 후 자동으로 숨기기
            setTimeout(() => {
                celebration.style.display = 'none';
            }, 5000);
        }
    }
    
    hideLoadingMessage() {
        const loadingMessage = document.getElementById('loadingMessage');
        if (loadingMessage) {
            loadingMessage.style.display = 'none';
        }
    }
    
    toggleInput(enabled) {
        const isMobile = window.innerWidth <= 768;
        const elements = [
            { id: 'messageInput', focus: !isMobile && enabled },
            { id: 'sendBtn', focus: false },
            { id: 'messageInputMobile', focus: isMobile && enabled },
            { id: 'sendBtnMobile', focus: false }
        ];
        
        elements.forEach(({ id, focus }) => {
            const element = document.getElementById(id);
            if (element) {
                element.disabled = !enabled;
                if (focus) {
                    element.focus();
                }
            }
        });
    }
    
    enableInput() {
        this.toggleInput(true);
    }
    
    disableInput() {
        this.toggleInput(false);
    }
}

// 유틸리티 함수들
const chatUtils = {
    // 메시지 시간 포맷팅
    formatTime(date = new Date()) {
        return date.toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    },
    
    // 텍스트 길이 체크
    isValidMessage(message) {
        return message.trim().length > 0 && message.length <= 1000;
    },
    
    // 키보드 단축키 도움말
    showKeyboardHelp() {
        alert('키보드 단축키:\\n- Enter: 메시지 전송\\n- Shift + Enter: 줄바꿈');
    }
};

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    new SocraticChatHandler();
});
