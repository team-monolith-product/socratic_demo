// Teacher Setup Page JavaScript
// Handles session creation and navigation to dashboard

class TeacherSetup {
    constructor() {
        this.sessionManager = new SimplifiedSessionManager();
        this.qrGenerator = new QRGenerator();

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
            this.showLoading(true, '세션을 생성하고 있습니다...');

            const formData = new FormData(event.target);
            const sessionConfig = {
                title: formData.get('title'),
                topic: formData.get('topic'),
                difficulty: formData.get('difficulty'),
                show_score: formData.get('showScore') === 'true'
            };

            console.log('Creating session with config:', sessionConfig);

            // Create session
            const result = await this.sessionManager.createSession(sessionConfig);

            if (result && result.session) {
                console.log('Session created successfully:', result);

                // Navigate to dashboard with the new session
                this.goToDashboard(result.session.id);
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

    goToDashboard(sessionId) {
        // Navigate to the dashboard page
        const dashboardUrl = `/pages/teacher-dashboard.html?session=${sessionId}`;
        console.log('Navigating to dashboard:', dashboardUrl);
        window.location.href = dashboardUrl;
    }

    showLoading(show, message = '처리 중입니다...') {
        const loading = document.getElementById('loading');
        const loadingMessage = document.getElementById('loadingMessage');

        if (loading) {
            loading.style.display = show ? 'flex' : 'none';
            if (loadingMessage && message) {
                loadingMessage.textContent = message;
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