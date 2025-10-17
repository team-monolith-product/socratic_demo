// Student Session JavaScript

class StudentSession {
    constructor() {
        this.apiBaseUrl = window.__API_BASE__ || '/api/v1';
        this.sessionId = null;
        this.sessionData = null;
        this.studentName = null;
        this.studentToken = null;

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

    // Token management methods
    getStoredStudentToken() {
        const key = `student_token_${this.sessionId}`;
        return localStorage.getItem(key);
    }

    setStudentToken(token) {
        const key = `student_token_${this.sessionId}`;
        localStorage.setItem(key, token);
        this.studentToken = token;
    }

    getStoredStudentName() {
        const key = `student_name_${this.sessionId}`;
        return localStorage.getItem(key);
    }

    setStoredStudentName(name) {
        const key = `student_name_${this.sessionId}`;
        localStorage.setItem(key, name);
    }

    clearStoredData() {
        const tokenKey = `student_token_${this.sessionId}`;
        const nameKey = `student_name_${this.sessionId}`;
        localStorage.removeItem(tokenKey);
        localStorage.removeItem(nameKey);
    }

    checkForStoredData() {
        // Pre-fill name if stored
        const storedName = this.getStoredStudentName();
        const storedToken = this.getStoredStudentToken();

        if (storedName && storedToken) {
            console.log(`🔄 Found stored data - Name: ${storedName}, Token: ${storedToken?.substring(0, 8)}...`);

            // Auto-fill the name input when it becomes available
            setTimeout(() => {
                const nameInput = document.getElementById('student-name');
                if (nameInput) {
                    nameInput.value = storedName;
                    this.validateInput(); // Enable join button if name is valid
                }
            }, 100);
        }
    }


    async init() {
        console.log('Initializing Student Session...', this.sessionId);

        try {
            // Load session info
            await this.loadSessionInfo();

            // Setup event listeners
            this.setupEventListeners();

            // Pre-fill name if stored and check for auto-reconnection
            this.checkForStoredData();

            // Always show session info screen (require name input)
            this.showSessionInfo();

        } catch (error) {
            console.error('Failed to initialize student session:', error);
            const technicalInfo = `
Session ID: ${this.sessionId}
API URL: ${this.apiBaseUrl}
Error: ${error.message}
Type: ${error.constructor.name}
Online: ${navigator.onLine}
URL: ${window.location.href}
            `.trim();
            this.showError('세션 정보를 불러올 수 없습니다.', technicalInfo);
        }
    }

    async loadSessionInfo() {
        try {
            console.log('Loading session info for:', this.sessionId);
            console.log('API Base URL:', this.apiBaseUrl);

            // Use public session API for students
            const response = await fetch(`${this.apiBaseUrl}/session/${this.sessionId}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const sessionInfo = await response.json();

            // Public API returns flat structure, wrap to match expected structure
            this.sessionData = {
                config: {
                    topic: sessionInfo.session.topic,
                    description: sessionInfo.session.description,
                    difficulty: sessionInfo.session.difficulty,
                    show_score: sessionInfo.session.show_score
                }
            };
            console.log('Session data loaded:', this.sessionData);
        } catch (error) {
            console.error('Failed to load session info:', error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack,
                sessionId: this.sessionId,
                apiBaseUrl: this.apiBaseUrl
            });
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
        const errorDiv = document.getElementById('name-error');

        if (studentNameInput && joinButton) {
            const isValid = studentNameInput.value.trim().length >= 2;
            joinButton.disabled = !isValid;

            // Clear error message and reset input style when user types
            if (errorDiv) {
                errorDiv.textContent = '';
                studentNameInput.style.borderColor = '';
            }
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
            // Join session via API (token + name-based matching)
            const storedToken = this.getStoredStudentToken();
            const requestBody = {
                student_name: this.studentName,
                student_token: storedToken  // Include stored token for reconnection
            };

            const response = await fetch(`${this.apiBaseUrl}/session/${this.sessionId}/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const error = new Error(errorData.detail || `HTTP ${response.status}`);

                // Check for specific error types
                if (response.status === 400 && errorData.detail?.includes('이미 사용중')) {
                    error.type = 'name_taken';
                    error.message = '이미 사용중인 이름입니다. 다른 이름을 입력해주세요.';
                }

                throw error;
            }

            const joinResponse = await response.json();
            console.log('Successfully joined session:', joinResponse);

            // Store student_id and token from response
            this.studentId = joinResponse.student_id;
            this.studentToken = joinResponse.student_token;
            this.currentScore = joinResponse.understanding_score || 0;

            // Save token and name to localStorage for re-entry
            this.setStudentToken(joinResponse.student_token);
            this.setStoredStudentName(this.studentName);

            // Redirect to chat interface
            this.redirectToChatInterface();

        } catch (error) {
            console.error('Failed to join session:', error);

            // Handle specific error types
            if (error.type === 'name_taken') {
                // Show error message for duplicate name
                const nameInput = document.getElementById('student-name');
                const errorDiv = document.getElementById('name-error');

                // Create error message element if it doesn't exist
                if (!errorDiv) {
                    const errorMessage = document.createElement('div');
                    errorMessage.id = 'name-error';
                    errorMessage.className = 'error-message';
                    errorMessage.style.color = '#dc3545';
                    errorMessage.style.fontSize = '14px';
                    errorMessage.style.marginTop = '5px';
                    nameInput.parentNode.insertBefore(errorMessage, nameInput.nextSibling);
                }

                document.getElementById('name-error').textContent = error.message;
                nameInput.style.borderColor = '#dc3545';
                nameInput.focus();
                nameInput.select();

            } else {
                alert('세션 참여에 실패했습니다. 다시 시도해주세요.');
            }

            joinButton.disabled = false;
            joinButton.textContent = '세션 참여하기';
        }
    }

    redirectToChatInterface() {
        // Redirect to the main socratic chat interface with session configuration
        const config = this.sessionData.config || {};
        const params = new URLSearchParams({
            session_id: this.sessionId,
            student_id: this.studentId,
            student_name: encodeURIComponent(this.studentName),
            topic: config.topic || '소크라테스 학습',
            difficulty: config.difficulty || 'normal',
            showScore: config.show_score || false,
            mode: 'student',
            currentScore: this.currentScore || 0  // Include current score for returning students
        });

        const chatUrl = `/chat?${params.toString()}`;
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

        // Auto-focus on name input field (especially for mobile keyboard)
        setTimeout(() => {
            const studentNameInput = document.getElementById('student-name');
            if (studentNameInput) {
                studentNameInput.focus();
            }
        }, 100); // Small delay to ensure DOM is ready
    }

    populateSessionInfo() {
        const config = this.sessionData.config || {};
        const elements = {
            'session-topic': config.topic || '소크라테스 세션',
            'session-description': config.description || '소크라테스 방식으로 학습해보세요.',
            'session-difficulty': this.getDifficultyText(config.difficulty),
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


    showError(message, technicalDetails = null) {
        // Hide loading screen
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) loadingScreen.classList.add('hidden');

        // Show error screen
        const errorScreen = document.getElementById('error-screen');
        const errorMessage = document.getElementById('error-message');

        if (errorScreen) errorScreen.classList.remove('hidden');
        if (errorMessage) {
            errorMessage.innerHTML = `
                <p>${message}</p>
                ${technicalDetails ? `<details style="margin-top: 1rem; text-align: left;">
                    <summary style="cursor: pointer; color: #666;">기술적 세부사항</summary>
                    <pre style="background: #f8f9fa; padding: 1rem; border-radius: 4px; margin-top: 0.5rem; overflow-x: auto; font-size: 0.8rem;">${technicalDetails}</pre>
                </details>` : ''}
            `;
        }
    }
}

// Initialize when script loads
new StudentSession();