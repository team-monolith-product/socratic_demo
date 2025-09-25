// Teacher Dashboard Page JavaScript
// Handles dashboard functionality and real-time updates

class TeacherDashboard {
    constructor() {
        this.sessionManager = new SimplifiedSessionManager();
        this.qrGenerator = new QRGenerator();
        this.autoRefreshInterval = null;
        this.currentSessionId = null;
        this.isRefreshing = false;
        this.lastUpdateTime = null;

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
        console.log('Initializing Teacher Dashboard...');

        try {
            // Set up event listeners
            this.setupEventListeners();

            // Get session ID from URL or localStorage
            const sessionId = this.getSessionIdFromUrl() || this.getSessionIdFromStorage();

            if (!sessionId) {
                this.redirectToSetup('세션 정보가 없습니다');
                return;
            }

            this.currentSessionId = sessionId;

            // Load and display dashboard
            await this.loadDashboard(sessionId);

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showError('대시보드 초기화에 실패했습니다: ' + error.message);
        }
    }

    getSessionIdFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('session');
    }

    getSessionIdFromStorage() {
        const savedSession = this.sessionManager.getSavedSession();
        return savedSession ? savedSession.sessionId : null;
    }

    setupEventListeners() {
        // Dashboard action buttons
        const showQRBtn = document.getElementById('showQRBtn');
        if (showQRBtn) {
            showQRBtn.addEventListener('click', () => this.showQRCode());
        }

        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.manualRefresh());
        }

        const newSessionBtn = document.getElementById('newSessionBtn');
        if (newSessionBtn) {
            newSessionBtn.addEventListener('click', () => this.showNewSessionConfirmation());
        }

        // QR Modal actions
        const copyLinkBtn = document.getElementById('copyLinkBtn');
        if (copyLinkBtn) {
            copyLinkBtn.addEventListener('click', () => this.copySessionLink());
        }

        const downloadQRBtn = document.getElementById('downloadQRBtn');
        if (downloadQRBtn) {
            downloadQRBtn.addEventListener('click', () => this.downloadQRCode());
        }

        const closeFocusBtn = document.getElementById('closeFocusBtn');
        if (closeFocusBtn) {
            closeFocusBtn.addEventListener('click', () => this.closeModal(document.getElementById('qrModal')));
        }

        // New session confirmation
        const confirmNewSession = document.getElementById('confirmNewSession');
        if (confirmNewSession) {
            confirmNewSession.addEventListener('click', () => this.confirmNewSession());
        }

        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(button => {
            button.addEventListener('click', (e) => this.closeModal(e.target.closest('.modal')));
        });

        // Modal overlay click to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal);
                }
            });
        });

        // Cancel buttons
        document.querySelectorAll('[data-action="cancel"]').forEach(button => {
            button.addEventListener('click', (e) => this.closeModal(e.target.closest('.modal')));
        });

        // Student search
        const studentSearch = document.getElementById('studentSearch');
        if (studentSearch) {
            studentSearch.addEventListener('input', (e) => this.filterStudents(e.target.value));
        }

        // Debug: Add clear localStorage handler for development
        if (window.location.hostname === 'localhost') {
            document.addEventListener('keydown', (e) => {
                if (e.key === 'F9') {
                    console.log('Clearing localStorage (F9 pressed)');
                    this.sessionManager.clearSavedSession();
                    this.redirectToSetup('세션이 초기화되었습니다');
                }
            });
        }
    }

    async loadDashboard(sessionId) {
        try {
            // Validate session exists
            const isValid = await this.sessionManager.validateSession(sessionId);

            if (!isValid) {
                throw new Error('유효하지 않은 세션입니다');
            }

            // Load session details
            await this.loadSessionDetails();

            // Start auto-refresh
            this.startAutoRefresh();

        } catch (error) {
            console.error('Failed to load dashboard:', error);

            // Try to use localStorage data as fallback
            const savedSession = this.sessionManager.getSavedSession();
            if (savedSession && savedSession.sessionId === sessionId) {
                console.log('Using localStorage data as fallback');
                this.showLocalStorageData(savedSession);
                this.startAutoRefresh(); // Still try auto-refresh for future updates
            } else {
                throw error;
            }
        }
    }

    async loadSessionDetails() {
        if (!this.currentSessionId) return;

        try {
            const sessionDetails = await this.sessionManager.getSessionDetails(this.currentSessionId);
            this.updateDashboardData(sessionDetails);
            this.updateLastRefreshTime();
        } catch (error) {
            console.error('Failed to load session details:', error);
            throw error;
        }
    }

    updateDashboardData(sessionDetails) {
        const session = sessionDetails.session;
        const stats = session.live_stats || {};
        const students = sessionDetails.students || [];

        console.log('Updating dashboard with:', { session, stats, students });

        // Calculate real data from students
        const realStudentCount = students.length;
        const totalMessages = students.reduce((sum, s) => sum + (s.message_count || 0), 0);

        // Calculate average score from actual student scores
        let realAverageScore = 0;
        if (students.length > 0) {
            const totalScore = students.reduce((sum, s) => sum + (s.latest_score || 0), 0);
            realAverageScore = Math.round(totalScore / students.length);
        }

        // Update session title
        const sessionTitleElement = document.getElementById('sessionTitleDisplay');
        if (sessionTitleElement) {
            const title = (session.config && session.config.title) ||
                         (session.title) ||
                         '세션';

            sessionTitleElement.textContent = title;
            console.log('Session title updated to:', title);
        }

        // Update statistics cards
        document.getElementById('studentCount').textContent = realStudentCount;
        document.getElementById('sessionDuration').textContent =
            this.sessionManager.calculateSessionDuration(session.created_at, session.duration_minutes);
        document.getElementById('averageScore').textContent = `${realAverageScore}%`;
        document.getElementById('totalMessages').textContent = totalMessages;

        // Update students table
        this.updateStudentsTable(students);
    }

    showLocalStorageData(sessionInfo) {
        console.log('Showing localStorage data:', sessionInfo);

        // Update session title
        const sessionTitleElement = document.getElementById('sessionTitleDisplay');
        if (sessionTitleElement && sessionInfo.title) {
            sessionTitleElement.textContent = sessionInfo.title;
        }

        // Calculate session duration from creation time
        let sessionDuration = '0분';
        if (sessionInfo.createdAt) {
            const startTime = new Date(sessionInfo.createdAt);
            const now = new Date();
            const diffMs = now - startTime;
            const diffMinutes = Math.floor(diffMs / (1000 * 60));
            sessionDuration = this.sessionManager.formatDuration(Math.max(0, diffMinutes));
        }

        // Set basic stats (no students data available from localStorage)
        document.getElementById('studentCount').textContent = '0';
        document.getElementById('sessionDuration').textContent = sessionDuration;
        document.getElementById('averageScore').textContent = '0%';
        document.getElementById('totalMessages').textContent = '0';

        // Show empty students table
        this.updateStudentsTable([]);

        // Update last refresh time
        this.updateLastRefreshTime();
    }

    updateStudentsTable(students) {
        const tableBody = document.getElementById('studentsTableBody');
        const emptyState = document.getElementById('tableEmptyState');

        if (students.length === 0) {
            tableBody.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';
        tableBody.innerHTML = students.map((student, index) => `
            <tr>
                <td>${student.student_name || `학생 #${String(index + 1).padStart(3, '0')}`}</td>
                <td>${this.createScoreBar(student.latest_score || 0)}</td>
                <td>${student.message_count || 0}개</td>
                <td>${this.formatLastActivity(student.minutes_since_last_activity)}</td>
            </tr>
        `).join('');
    }

    createScoreBar(score) {
        const percentage = Math.round(score);

        // Determine score category and color
        let category = 'poor';
        if (percentage >= 80) category = 'excellent';
        else if (percentage >= 60) category = 'good';

        return `
            <div class="score-bar-container">
                <div class="score-bar">
                    <div class="score-bar-fill ${category}" style="width: ${percentage}%"></div>
                </div>
                <div class="score-text">${percentage}%</div>
            </div>
        `;
    }

    formatLastActivity(minutes) {
        if (minutes === undefined || minutes === null) return '-';
        if (minutes === 0) return '방금 전';
        if (minutes < 60) return `${minutes}분 전`;
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        if (remainingMinutes === 0) return `${hours}시간 전`;
        return `${hours}시간 ${remainingMinutes}분 전`;
    }

    filterStudents(searchTerm) {
        const rows = document.querySelectorAll('#studentsTableBody tr');
        const term = searchTerm.toLowerCase();

        rows.forEach(row => {
            const studentName = row.querySelector('td:first-child').textContent.toLowerCase();
            if (studentName.includes(term)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // Auto-refresh Management
    startAutoRefresh() {
        // Stop any existing refresh
        this.stopAutoRefresh();

        // Start auto-refresh every 10 seconds
        this.autoRefreshInterval = setInterval(() => {
            this.autoRefresh();
        }, 10000);

        console.log('Auto-refresh started');
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('Auto-refresh stopped');
        }
    }

    async autoRefresh() {
        if (this.isRefreshing || !this.currentSessionId) {
            return;
        }

        try {
            this.isRefreshing = true;
            this.showRefreshIndicator(true);

            await this.loadSessionDetails();

        } catch (error) {
            console.error('Auto-refresh failed:', error);
        } finally {
            this.isRefreshing = false;
            this.showRefreshIndicator(false);
        }
    }

    async manualRefresh() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = `
                <span class="btn-icon">⏳</span>
                새로고침 중...
            `;
        }

        try {
            await this.loadSessionDetails();
            this.showToast('✅ 대시보드가 업데이트되었습니다', 'success');
        } catch (error) {
            console.error('Manual refresh failed:', error);
            this.showToast('❌ 새로고침에 실패했습니다', 'error');
        } finally {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = `
                    <span class="btn-icon">🔄</span>
                    새로고침
                `;
            }
        }
    }

    showRefreshIndicator(show) {
        // Add subtle refresh indicator to statistics cards
        const statsCards = document.querySelectorAll('.stat-card');
        statsCards.forEach(card => {
            if (show) {
                card.style.opacity = '0.7';
            } else {
                card.style.opacity = '1';
            }
        });
    }

    updateLastRefreshTime() {
        this.lastUpdateTime = new Date();
        const timeDisplay = document.getElementById('lastUpdateTime');

        if (timeDisplay) {
            const timeStr = this.lastUpdateTime.toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            timeDisplay.textContent = `마지막 업데이트: ${timeStr}`;
        }
    }

    // QR Code Management
    async showQRCode() {
        if (!this.currentSessionId) {
            this.showError('현재 활성 세션이 없습니다');
            return;
        }

        try {
            this.showLoading(true, 'QR 코드를 생성하고 있습니다...');

            // Get session info
            const savedSession = this.sessionManager.getSavedSession();
            if (!savedSession) {
                throw new Error('세션 정보를 찾을 수 없습니다');
            }

            // Generate QR code
            const qrImageData = await this.sessionManager.generateSessionQR(this.currentSessionId);

            // Create session data for modal
            const base_url = window.location.origin;
            const session_url = `${base_url}/s/${this.currentSessionId}`;

            const sessionData = {
                session: {
                    id: this.currentSessionId,
                    config: {
                        title: savedSession.title,
                        topic: savedSession.topic,
                        difficulty: savedSession.difficulty,
                        show_score: savedSession.showScore
                    },
                    created_at: savedSession.createdAt
                },
                qr_code: {
                    url: session_url,
                    image_data: qrImageData
                }
            };

            this.showQRModal(sessionData);

        } catch (error) {
            console.error('Failed to show QR code:', error);
            this.showError('QR 코드를 표시할 수 없습니다: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    showQRModal(sessionData) {
        const modal = document.getElementById('qrModal');
        const qrCode = sessionData.qr_code;

        // Update modal content
        const sessionLink = document.getElementById('sessionLink');
        sessionLink.href = qrCode.url;
        sessionLink.textContent = qrCode.url;

        // Display QR code
        const qrCanvas = document.getElementById('qrCanvas');
        this.qrGenerator.displayQRCode(qrCanvas, qrCode.image_data);

        // Update session summary
        const config = sessionData.session.config;
        const sessionSummary = document.getElementById('sessionSummary');
        sessionSummary.innerHTML = `
            <div class="detail-item">
                <strong>📋 제목:</strong> ${config.title}
            </div>
            <div class="detail-item">
                <strong>📚 주제:</strong> ${config.topic}
            </div>
            <div class="detail-item">
                <strong>🎓 난이도:</strong> ${this.sessionManager.getDifficultyText(config.difficulty)}
            </div>
            <div class="detail-item">
                <strong>📊 점수표시:</strong> ${config.show_score ? '보기' : '숨김'}
            </div>
            <div class="detail-item">
                <strong>📅 생성시간:</strong> ${this.sessionManager.formatKoreanTime(sessionData.session.created_at)}
            </div>
        `;

        // Store current session data for modal actions
        this.currentModalSession = sessionData;

        // Show modal
        modal.style.display = 'flex';
    }

    async copySessionLink() {
        if (!this.currentModalSession) return;

        const url = this.currentModalSession.qr_code.url;
        try {
            const success = await this.qrGenerator.copyToClipboard(url);
            if (success) {
                this.showToast('✅ 링크가 클립보드에 복사되었습니다', 'success');
            } else {
                this.showToast('❌ 링크 복사에 실패했습니다', 'error');
            }
        } catch (error) {
            console.error('Copy failed:', error);
            this.showToast('❌ 링크 복사에 실패했습니다', 'error');
        }
    }

    downloadQRCode() {
        if (!this.currentModalSession) return;

        const qrCanvas = document.getElementById('qrCanvas');
        const sessionId = this.currentModalSession.session.id;
        const filename = `session_${sessionId}_qr.png`;

        const success = this.qrGenerator.downloadQRCode(qrCanvas, filename);
        if (success) {
            this.showToast('✅ QR 코드가 다운로드되었습니다', 'success');
        } else {
            this.showToast('❌ QR 코드 다운로드에 실패했습니다', 'error');
        }
    }

    // New Session Flow
    showNewSessionConfirmation() {
        const modal = document.getElementById('confirmNewSessionModal');
        modal.style.display = 'flex';
    }

    async confirmNewSession() {
        try {
            this.showLoading(true, '새 세션을 준비하고 있습니다...');

            // Archive current session and redirect to setup
            await this.sessionManager.startNewSession();

            this.closeModal(document.getElementById('confirmNewSessionModal'));

            // Redirect to setup page
            this.redirectToSetup('새 세션을 시작할 수 있습니다');

        } catch (error) {
            console.error('Failed to start new session:', error);
            this.showError('새 세션 시작에 실패했습니다: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    // Utility Methods
    closeModal(modal) {
        if (modal) {
            modal.style.display = 'none';
        }
    }

    redirectToSetup(message) {
        if (message) {
            // Store message to show after redirect
            sessionStorage.setItem('setupMessage', message);
        }
        window.location.href = '/pages/teacher-setup.html';
    }

    showLoading(show, message = '처리 중입니다...') {
        const loading = document.getElementById('loading');
        const loadingMessage = document.getElementById('loadingMessage');

        if (loading) {
            loading.style.display = show ? 'flex' : 'none';
            if (loadingMessage) {
                loadingMessage.textContent = message;
            }
        }
    }

    showToast(message, type = 'success') {
        // Create and show toast notification
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Remove toast after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    showError(message) {
        this.showToast(message, 'error');
    }
}

// Initialize dashboard when script loads
const teacherDashboard = new TeacherDashboard();