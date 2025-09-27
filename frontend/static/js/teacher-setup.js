// Teacher Setup Page JavaScript
// Handles session creation and navigation to dashboard

class TeacherSetup {
    constructor() {
        this.sessionManager = new SimplifiedSessionManager();
        this.qrGenerator = new QRGenerator();
        this.lottieAnimation = null;

        // Set up QR generator dependency
        this.sessionManager.setQRGenerator(this.qrGenerator);

        // Initialize when DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    async init() {
        console.log('Initializing Teacher Setup...');

        try {
            // Set up event listeners
            this.setupEventListeners();

            // Check if there's an existing session
            await this.checkExistingSession();

        } catch (error) {
            console.error('Failed to initialize setup:', error);
            this.showError('초기화에 실패했습니다: ' + error.message);
        }
    }

    setupEventListeners() {
        // Session setup form
        const sessionForm = document.getElementById('sessionForm');
        if (sessionForm) {
            sessionForm.addEventListener('submit', (e) => this.handleSessionCreate(e));
        }

        // Debug: Add clear localStorage handler for development
        if (window.location.hostname === 'localhost') {
            document.addEventListener('keydown', (e) => {
                if (e.key === 'F9') {
                    console.log('Clearing localStorage (F9 pressed)');
                    this.sessionManager.clearSavedSession();
                    location.reload();
                }
            });
        }
    }

    async checkExistingSession() {
        // Check if there's already an active session
        const savedSession = this.sessionManager.getSavedSession();

        if (savedSession) {
            console.log('Found existing session:', savedSession);

            try {
                // Validate the session with server
                const isValid = await this.sessionManager.validateSession(savedSession.sessionId);

                if (isValid) {
                    // Show option to continue existing session
                    this.showExistingSessionOption(savedSession);
                } else {
                    // Clear invalid session
                    this.sessionManager.clearSavedSession();
                }
            } catch (error) {
                console.warn('Could not validate session:', error);
                // Continue with setup anyway
            }
        }
    }

    showExistingSessionOption(sessionInfo) {
        // Create a banner to show existing session option
        const banner = document.createElement('div');
        banner.className = 'existing-session-banner';
        banner.innerHTML = `
            <div class="banner-content">
                <div class="banner-info">
                    <h3>기존 세션이 있습니다</h3>
                    <p>"${sessionInfo.title}" 세션이 진행 중입니다</p>
                </div>
                <div class="banner-actions">
                    <button class="secondary-button" id="continueSession">대시보드로 이동</button>
                    <button class="tertiary-button" id="createNewSession">새 세션 만들기</button>
                </div>
            </div>
        `;

        // Insert before main content
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.insertBefore(banner, mainContent.firstChild);
        }

        // Add event listeners
        document.getElementById('continueSession')?.addEventListener('click', () => {
            this.goToDashboard(sessionInfo.sessionId);
        });

        document.getElementById('createNewSession')?.addEventListener('click', () => {
            banner.remove();
            this.sessionManager.clearSavedSession();
        });

        // Add banner styles dynamically
        const style = document.createElement('style');
        style.textContent = `
            .existing-session-banner {
                background: linear-gradient(135deg, #3574d9, #2a5bb8);
                color: white;
                padding: 24px;
                border-radius: 16px;
                margin-bottom: 32px;
            }
            .banner-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 24px;
            }
            .banner-info h3 {
                margin: 0 0 4px 0;
                font-size: 18px;
                font-weight: 600;
            }
            .banner-info p {
                margin: 0;
                opacity: 0.9;
                font-size: 14px;
            }
            .banner-actions {
                display: flex;
                gap: 12px;
                flex-shrink: 0;
            }
            .secondary-button, .tertiary-button {
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                border: none;
                font-family: 'Pretendard', sans-serif;
            }
            .secondary-button {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            .secondary-button:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            .tertiary-button {
                background: transparent;
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            .tertiary-button:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            @media (max-width: 768px) {
                .banner-content {
                    flex-direction: column;
                    align-items: flex-start;
                }
                .banner-actions {
                    width: 100%;
                    justify-content: flex-start;
                }
            }
        `;
        document.head.appendChild(style);
    }

    async handleSessionCreate(event) {
        event.preventDefault();

        try {
            const formData = new FormData(event.target);

            // PDF 기능과 통합된 세션 설정 구성
            const sessionConfig = await this.buildSessionConfig(formData);

            console.log('Creating session with config:', sessionConfig);

            // 로딩 표시
            this.showLoading(true, '세션을 생성하는 중...');

            // Create session
            const result = await this.sessionManager.createSession(sessionConfig);

            if (result && result.session) {
                console.log('Session created successfully:', result);

                // Navigate to dashboard with the new session
                this.goToDashboard(result.session.id, true);
            } else {
                throw new Error('세션 생성 응답이 올바르지 않습니다');
            }

        } catch (error) {
            console.error('Failed to create session:', error);
            this.showError('세션 생성에 실패했습니다: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async buildSessionConfig(formData) {
        // 기본 세션 설정
        const sessionConfig = {
            title: formData.get('title'),
            topic: formData.get('topic') || '', // PDF 시스템에서 설정됨
            difficulty: formData.get('difficulty'),
            show_score: formData.get('showScore') === 'true',
            // PDF 관련 정보 추가
            source_type: 'manual',
            pdf_content: null,
            manual_content: null,
            combined_topic: null,
            key_concepts: null,
            learning_objectives: null
        };

        // PDF 기능이 활성화되어 있는 경우 상태 확인
        if (window.pdfTopicManager) {
            const pdfState = window.pdfTopicManager.state;

            if (pdfState.pdfContent || pdfState.manualContent) {
                // PDF 콘텐츠가 있는 경우
                if (pdfState.pdfContent && pdfState.manualContent) {
                    sessionConfig.source_type = 'hybrid';
                    sessionConfig.pdf_content = pdfState.pdfContent;
                    sessionConfig.manual_content = pdfState.manualContent;
                } else if (pdfState.pdfContent) {
                    sessionConfig.source_type = 'pdf';
                    sessionConfig.pdf_content = pdfState.pdfContent;
                } else {
                    sessionConfig.source_type = 'manual';
                    sessionConfig.manual_content = pdfState.manualContent;
                }

                // 최종 주제가 있으면 사용
                if (pdfState.finalTopic) {
                    sessionConfig.topic = pdfState.finalTopic;
                    sessionConfig.combined_topic = pdfState.finalTopic;
                }
            }
        }

        // topic이 비어있으면 에러
        if (!sessionConfig.topic || sessionConfig.topic.trim() === '') {
            throw new Error('학습 주제를 입력하거나 PDF를 업로드해주세요.');
        }

        return sessionConfig;
    }

    goToDashboard(sessionId, isNewSession = false) {
        // Navigate to the dashboard page
        let dashboardUrl = `/pages/teacher-dashboard.html?session=${sessionId}`;

        // Add newSession parameter if this is a newly created session
        if (isNewSession) {
            dashboardUrl += '&newSession=true';
        }

        console.log('Navigating to dashboard:', dashboardUrl);
        window.location.href = dashboardUrl;
    }

    showLoading(show, message = '처리 중입니다...') {
        const loading = document.getElementById('loading');
        const loadingMessage = document.getElementById('loadingMessage');
        const lottieContainer = document.getElementById('lottie-container');

        if (loading) {
            loading.style.display = show ? 'flex' : 'none';
            if (loadingMessage && message) {
                loadingMessage.textContent = message;
            }

            if (show && lottieContainer && !this.lottieAnimation) {
                // Load Lottie animation
                this.lottieAnimation = lottie.loadAnimation({
                    container: lottieContainer,
                    renderer: 'svg',
                    loop: true,
                    autoplay: true,
                    path: '/static/002 lottie.json'
                });
            } else if (!show && this.lottieAnimation) {
                // Clean up animation when hiding
                this.lottieAnimation.destroy();
                this.lottieAnimation = null;
            }
        }
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'success') {
        // Create and show toast notification
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        // Add toast styles if not already present
        if (!document.querySelector('#toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 16px 24px;
                    border-radius: 8px;
                    color: white;
                    font-weight: 500;
                    font-size: 14px;
                    z-index: 10000;
                    animation: slideInRight 0.3s ease;
                    max-width: 400px;
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                }
                .toast.success {
                    background: #10b981;
                }
                .toast.error {
                    background: #ef4444;
                }
                @keyframes slideInRight {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(toast);

        // Remove toast after 4 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }
        }, 4000);
    }
}

// Initialize the setup when script loads
const teacherSetup = new TeacherSetup();