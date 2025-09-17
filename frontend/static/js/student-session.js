// Student Session JavaScript

class StudentSession {
    constructor() {
        this.sessionManager = new SessionManager();
        this.sessionId = null;
        this.sessionData = null;
        this.studentName = null;

        // Get session ID from URL
        this.sessionId = this.extractSessionIdFromUrl();

        if (!this.sessionId) {
            this.showError('유효하지 않은 세션 링크입니다.');
            return;
        }

        // Initialize when DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    extractSessionIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/s\/([^\/]+)/);
        return match ? match[1] : null;
    }

    async init() {
        console.log('Initializing Student Session...', this.sessionId);

        try {
            // Load session info
            await this.loadSessionInfo();

            // Setup event listeners
            this.setupEventListeners();

            // Show session info screen
            this.showSessionInfo();

        } catch (error) {
            console.error('Failed to initialize student session:', error);
            this.showError('세션 정보를 불러올 수 없습니다.');
        }
    }

    async loadSessionInfo() {
        try {
            const sessionDetails = await this.sessionManager.getSessionDetails(this.sessionId);
            this.sessionData = sessionDetails.session;
            console.log('Session data loaded:', this.sessionData);
        } catch (error) {
            console.error('Failed to load session info:', error);
            throw new Error('세션을 찾을 수 없습니다.');
        }
    }

    setupEventListeners() {
        const joinButton = document.getElementById('join-session-btn');
        const studentNameInput = document.getElementById('student-name');

        if (joinButton) {
            joinButton.addEventListener('click', () => this.handleJoinSession());
        }

        if (studentNameInput) {
            studentNameInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleJoinSession();
                }
            });

            studentNameInput.addEventListener('input', () => {
                this.validateInput();
            });
        }
    }

    validateInput() {
        const studentNameInput = document.getElementById('student-name');
        const joinButton = document.getElementById('join-session-btn');

        if (studentNameInput && joinButton) {
            const isValid = studentNameInput.value.trim().length >= 2;
            joinButton.disabled = !isValid;
        }
    }

    async handleJoinSession() {
        const studentNameInput = document.getElementById('student-name');
        const joinButton = document.getElementById('join-session-btn');

        if (!studentNameInput || !joinButton) return;

        const name = studentNameInput.value.trim();
        if (name.length < 2) {
            alert('이름을 2글자 이상 입력해주세요.');
            return;
        }

        this.studentName = name;
        joinButton.disabled = true;
        joinButton.textContent = '참여 중...';

        try {
            // Join session via API
            const joinResponse = await this.sessionManager.joinSession(this.sessionId, {
                student_name: this.studentName
            });

            console.log('Successfully joined session:', joinResponse);

            // Redirect to chat interface
            this.redirectToChatInterface();

        } catch (error) {
            console.error('Failed to join session:', error);
            alert('세션 참여에 실패했습니다. 다시 시도해주세요.');

            joinButton.disabled = false;
            joinButton.textContent = '세션 참여하기';
        }
    }

    redirectToChatInterface() {
        // Redirect to the main socratic chat interface with session configuration
        const params = new URLSearchParams({
            session_id: this.sessionId,
            student_name: encodeURIComponent(this.studentName),
            topic: this.sessionData.topic || '소크라테스 학습',
            difficulty: this.sessionData.difficulty || 'normal',
            show_score: this.sessionData.show_score || false,
            time_limit: this.sessionData.time_limit || 0,
            mode: 'student'
        });

        const chatUrl = `/pages/socratic-chat.html?${params.toString()}`;
        window.location.href = chatUrl;
    }

    showSessionInfo() {
        if (!this.sessionData) return;

        // Hide loading screen
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) loadingScreen.classList.add('hidden');

        // Show session info screen
        const sessionInfoScreen = document.getElementById('session-info-screen');
        if (sessionInfoScreen) sessionInfoScreen.classList.remove('hidden');

        // Populate session data
        this.populateSessionInfo();
    }

    populateSessionInfo() {
        const elements = {
            'session-topic': this.sessionData.topic || '소크라테스 세션',
            'session-description': this.sessionData.description || '소크라테스 방식으로 학습해보세요.',
            'session-difficulty': this.getDifficultyText(this.sessionData.difficulty),
            'session-time-limit': this.getTimeLimitText(this.sessionData.time_limit)
        };

        Object.entries(elements).forEach(([id, text]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = text;
        });
    }

    getDifficultyText(difficulty) {
        const difficultyMap = {
            'easy': '쉬움',
            'normal': '보통',
            'hard': '어려움'
        };
        return difficultyMap[difficulty] || '보통';
    }

    getTimeLimitText(timeLimit) {
        if (!timeLimit) return '제한 없음';
        return `${timeLimit}분`;
    }

    showError(message) {
        // Hide loading screen
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) loadingScreen.classList.add('hidden');

        // Show error screen
        const errorScreen = document.getElementById('error-screen');
        const errorMessage = document.getElementById('error-message');

        if (errorScreen) errorScreen.classList.remove('hidden');
        if (errorMessage) errorMessage.textContent = message;
    }
}

// Initialize when script loads
new StudentSession();