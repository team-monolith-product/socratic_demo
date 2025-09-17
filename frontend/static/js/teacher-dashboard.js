// Teacher Dashboard Main JavaScript

class TeacherDashboard {
    constructor() {
        this.sessionManager = new SessionManager();
        this.qrGenerator = new QRGenerator();
        this.sessions = [];
        this.refreshInterval = null;

        // Initialize when DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    async init() {
        console.log('Initializing Teacher Dashboard...');

        // Set up event listeners
        this.setupEventListeners();

        // Load initial data
        await this.loadSessions();

        // Start auto-refresh for active sessions
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Session creation form
        const sessionForm = document.getElementById('sessionForm');
        if (sessionForm) {
            sessionForm.addEventListener('submit', (e) => this.handleSessionCreate(e));
        }

        // Tab switching
        document.querySelectorAll('[data-tab]').forEach(tabButton => {
            tabButton.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

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

        // QR actions
        const copyLinkBtn = document.getElementById('copyLinkBtn');
        if (copyLinkBtn) {
            copyLinkBtn.addEventListener('click', () => this.copySessionLink());
        }

        const downloadQRBtn = document.getElementById('downloadQRBtn');
        if (downloadQRBtn) {
            downloadQRBtn.addEventListener('click', () => this.downloadQRCode());
        }

        const monitorSessionBtn = document.getElementById('monitorSessionBtn');
        if (monitorSessionBtn) {
            monitorSessionBtn.addEventListener('click', () => this.openSessionMonitoring());
        }
    }

    async handleSessionCreate(event) {
        event.preventDefault();

        try {
            this.showLoading(true);

            const formData = new FormData(event.target);
            const sessionConfig = {
                topic: formData.get('topic'),
                description: formData.get('description') || null,
                difficulty: formData.get('difficulty'),
                show_score: formData.get('showScore') === 'true',
                time_limit: parseInt(formData.get('timeLimit')),
                max_students: parseInt(formData.get('maxStudents'))
            };

            console.log('Creating session with config:', sessionConfig);

            const result = await this.sessionManager.createSession(sessionConfig);
            console.log('Session created successfully:', result);

            // Show QR code modal
            this.showQRModal(result);

            // Reset form
            event.target.reset();

            // Refresh sessions list
            await this.loadSessions();

        } catch (error) {
            console.error('Failed to create session:', error);
            this.showError('세션 생성에 실패했습니다: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    showQRModal(sessionData) {
        const modal = document.getElementById('qrModal');
        const sessionId = sessionData.session.id;
        const qrCode = sessionData.qr_code;

        // Update modal content
        document.getElementById('sessionId').textContent = sessionId;

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
            <div class="summary-item">
                <strong>📚 주제:</strong> ${config.topic}
            </div>
            ${config.description ? `<div class="summary-item"><strong>📖 설명:</strong> ${config.description}</div>` : ''}
            <div class="summary-item">
                <strong>🎓 난이도:</strong> ${this.sessionManager.getDifficultyText(config.difficulty)}
            </div>
            <div class="summary-item">
                <strong>📊 점수표시:</strong> ${config.show_score ? '보기' : '숨김'}
            </div>
            <div class="summary-item">
                <strong>⏱️ 제한시간:</strong> ${this.sessionManager.formatDuration(config.time_limit)}
            </div>
            <div class="summary-item">
                <strong>👥 최대인원:</strong> ${config.max_students}명
            </div>
            <div class="summary-item">
                <strong>📅 생성시간:</strong> ${new Date(sessionData.session.created_at).toLocaleString('ko-KR')}
            </div>
        `;

        // Store current session data for modal actions
        this.currentModalSession = sessionData;

        // Show modal
        modal.style.display = 'flex';
        modal.classList.add('fade-in');
    }

    async copySessionLink() {
        if (!this.currentModalSession) return;

        const url = this.currentModalSession.qr_code.url;
        try {
            const success = await this.qrGenerator.copyToClipboard(url);
            if (success) {
                this.showSuccess('링크가 클립보드에 복사되었습니다');
            } else {
                this.showError('링크 복사에 실패했습니다');
            }
        } catch (error) {
            console.error('Copy failed:', error);
            this.showError('링크 복사에 실패했습니다');
        }
    }

    downloadQRCode() {
        if (!this.currentModalSession) return;

        const qrCanvas = document.getElementById('qrCanvas');
        const sessionId = this.currentModalSession.session.id;
        const filename = `session_${sessionId}_qr.png`;

        const success = this.qrGenerator.downloadQRCode(qrCanvas, filename);
        if (success) {
            this.showSuccess('QR 코드가 다운로드되었습니다');
        } else {
            this.showError('QR 코드 다운로드에 실패했습니다');
        }
    }

    openSessionMonitoring() {
        if (!this.currentModalSession) return;

        const sessionId = this.currentModalSession.session.id;
        // Close QR modal first
        this.closeModal(document.getElementById('qrModal'));

        // Open monitoring modal
        this.showMonitoringModal(sessionId);
    }

    async showMonitoringModal(sessionId) {
        const modal = document.getElementById('monitorModal');
        const content = document.getElementById('monitorContent');

        try {
            this.showLoading(true);

            const sessionDetails = await this.sessionManager.getSessionDetails(sessionId);

            content.innerHTML = this.generateMonitoringHTML(sessionDetails);

            modal.style.display = 'flex';
            modal.classList.add('fade-in');

        } catch (error) {
            console.error('Failed to load session monitoring:', error);
            this.showError('세션 모니터링 데이터를 불러올 수 없습니다');
        } finally {
            this.showLoading(false);
        }
    }

    generateMonitoringHTML(sessionDetails) {
        const session = sessionDetails.session;
        const stats = sessionDetails.live_stats;
        const students = sessionDetails.students;

        return `
            <div class="monitoring-overview">
                <h4>📊 ${session.config.topic}</h4>
                <div class="overview-stats">
                    <div class="overview-stat">
                        <span class="stat-label">진행시간:</span>
                        <span class="stat-value">${this.calculateSessionDuration(session.created_at)}</span>
                    </div>
                    <div class="overview-stat">
                        <span class="stat-label">참여학생:</span>
                        <span class="stat-value">${stats.current_students}명 / ${session.config.max_students}명</span>
                    </div>
                    <div class="overview-stat">
                        <span class="stat-label">평균 이해도:</span>
                        <span class="stat-value">${Math.round(stats.average_score)}%</span>
                    </div>
                    <div class="overview-stat">
                        <span class="stat-label">완료율:</span>
                        <span class="stat-value">${Math.round(stats.completion_rate)}%</span>
                    </div>
                </div>
            </div>

            <div class="dimension-overview">
                <h5>🌊 5차원 평가 평균</h5>
                <div class="dimensions-grid">
                    ${Object.entries(stats.dimension_averages).map(([key, value]) => `
                        <div class="dimension-item">
                            <span class="dimension-name">${this.getDimensionName(key)}</span>
                            <div class="dimension-bar">
                                <div class="dimension-fill" style="width: ${value}%"></div>
                            </div>
                            <span class="dimension-value">${Math.round(value)}%</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="students-overview">
                <h5>👥 학생별 진행 상황</h5>
                <div class="students-list">
                    ${students.map((student, index) => `
                        <div class="student-item">
                            <div class="student-header">
                                <span class="student-name">학생 #${String(index + 1).padStart(3, '0')}</span>
                                <span class="student-progress ${this.getProgressClass(student.progress_percentage)}">
                                    ${student.progress_percentage}%
                                </span>
                            </div>
                            <div class="student-meta">
                                <span>대화: ${student.conversation_turns}턴</span>
                                <span>시간: ${student.time_spent}분</span>
                                <span>상태: ${student.is_completed ? '완료' : '진행중'}</span>
                            </div>
                            ${student.last_message ? `
                                <div class="student-last-message">
                                    최근: "${student.last_message}"
                                </div>
                            ` : ''}
                            <div class="student-dimensions">
                                ${Object.entries(student.current_dimensions).map(([key, value]) => `
                                    <span class="mini-dimension" title="${this.getDimensionName(key)}: ${value}%">
                                        ${this.getDimensionIcon(key)} ${value}%
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="monitoring-actions">
                <button class="action-btn" onclick="location.reload()">🔄 새로고침</button>
                <button class="action-btn danger" onclick="dashboard.endSessionFromMonitor('${session.id}')">⏹️ 세션 종료</button>
            </div>
        `;
    }

    async loadSessions() {
        try {
            const result = await this.sessionManager.getTeacherSessions();
            this.sessions = result.sessions;

            this.updateSessionsDisplay();

        } catch (error) {
            console.error('Failed to load sessions:', error);
            this.showError('세션 목록을 불러올 수 없습니다');
        }
    }

    updateSessionsDisplay() {
        const activeSessions = this.sessions.filter(s => s.status === 'active');
        const waitingSessions = this.sessions.filter(s => s.status === 'waiting');
        const completedSessions = this.sessions.filter(s => s.status === 'completed');

        // Update counts
        document.getElementById('activeSessionCount').textContent = activeSessions.length;
        document.getElementById('waitingSessionCount').textContent = waitingSessions.length;
        document.getElementById('completedSessionCount').textContent = completedSessions.length;

        // Update lists
        this.renderSessionsList('activeSessionsList', activeSessions);
        this.renderSessionsList('waitingSessionsList', waitingSessions);
        this.renderSessionsList('completedSessionsList', completedSessions);
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.session-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}SessionsList`).classList.add('active');
    }

    renderSessionsList(containerId, sessions) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (sessions.length === 0) {
            // Keep the existing empty state structure from HTML
            return;
        }

        // Replace empty state with session items
        container.innerHTML = sessions.map(session => this.generateSessionItemHTML(session)).join('');
    }

    generateSessionItemHTML(session) {
        const config = session.config;
        const stats = session.live_stats || {};

        return `
            <div class="session-item" data-session-id="${session.id}">
                <div class="session-header">
                    <div class="session-title">${config.topic}</div>
                    <div class="session-status" style="color: ${this.sessionManager.getStatusColor(session.status)}">
                        ${this.sessionManager.getStatusText(session.status)}
                    </div>
                </div>

                <div class="session-meta">
                    <span>${this.sessionManager.getDifficultyIcon(config.difficulty)} ${this.sessionManager.getDifficultyText(config.difficulty)}</span>
                    <span>⏱️ ${this.sessionManager.formatDuration(config.time_limit)}</span>
                    <span>👥 ${config.max_students}명</span>
                    <span>📅 ${this.sessionManager.formatTimestamp(session.created_at)}</span>
                </div>

                ${session.status === 'active' ? `
                    <div class="session-stats">
                        <div class="stat-item">👥 참여: ${stats.current_students || 0}명</div>
                        <div class="stat-item">📊 평균: ${Math.round(stats.average_score || 0)}%</div>
                        <div class="stat-item">✅ 완료율: ${Math.round(stats.completion_rate || 0)}%</div>
                    </div>
                ` : ''}

                <div class="session-actions">
                    ${this.generateSessionActions(session)}
                </div>
            </div>
        `;
    }

    generateSessionActions(session) {
        const actions = [];

        if (session.status === 'waiting') {
            actions.push(`<button class="action-btn" onclick="dashboard.showSessionQR('${session.id}')">🔗 QR보기</button>`);
            actions.push(`<button class="action-btn primary" onclick="dashboard.startSession('${session.id}')">▶️ 시작</button>`);
            actions.push(`<button class="action-btn danger" onclick="dashboard.deleteSession('${session.id}')">🗑️ 삭제</button>`);
        } else if (session.status === 'active') {
            actions.push(`<button class="action-btn primary" onclick="dashboard.monitorSession('${session.id}')">📊 모니터링</button>`);
            actions.push(`<button class="action-btn" onclick="dashboard.showSessionQR('${session.id}')">🔗 QR보기</button>`);
            actions.push(`<button class="action-btn danger" onclick="dashboard.endSession('${session.id}')">⏹️ 종료</button>`);
        } else if (session.status === 'completed') {
            actions.push(`<button class="action-btn" onclick="dashboard.viewSessionResults('${session.id}')">📈 결과보기</button>`);
            actions.push(`<button class="action-btn danger" onclick="dashboard.deleteSession('${session.id}')">🗑️ 삭제</button>`);
        }

        return actions.join('');
    }


    // Session action handlers
    async monitorSession(sessionId) {
        await this.showMonitoringModal(sessionId);
    }

    async endSession(sessionId) {
        if (!confirm('정말 세션을 종료하시겠습니까?')) return;

        try {
            this.showLoading(true);
            await this.sessionManager.endSession(sessionId);
            this.showSuccess('세션이 종료되었습니다');
            await this.loadSessions();
        } catch (error) {
            this.showError('세션 종료에 실패했습니다: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async deleteSession(sessionId) {
        if (!confirm('정말 세션을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;

        try {
            this.showLoading(true);
            await this.sessionManager.deleteSession(sessionId);
            this.showSuccess('세션이 삭제되었습니다');
            await this.loadSessions();
        } catch (error) {
            this.showError('세션 삭제에 실패했습니다: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }


    startAutoRefresh() {
        // Refresh every 30 seconds for active sessions
        this.refreshInterval = setInterval(() => {
            const hasActiveSessions = this.sessions.some(s => s.status === 'active');
            if (hasActiveSessions) {
                this.loadSessions();
            }
        }, 30000);
    }

    // Utility methods
    closeModal(modal) {
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('fade-in');
        }
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = show ? 'flex' : 'none';
        }
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `${type}-message`;
        messageEl.textContent = message;

        // Insert at top of main content
        const main = document.querySelector('.teacher-main');
        if (main) {
            main.insertBefore(messageEl, main.firstChild);

            // Auto remove after 5 seconds
            setTimeout(() => {
                if (messageEl.parentNode) {
                    messageEl.parentNode.removeChild(messageEl);
                }
            }, 5000);
        }
    }

    calculateSessionDuration(startTime) {
        const start = new Date(startTime);
        const now = new Date();
        const diffMs = now - start;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        return this.sessionManager.formatDuration(diffMinutes);
    }

    getDimensionName(key) {
        const names = {
            'depth': '사고 깊이',
            'breadth': '사고 확장',
            'application': '실생활 적용',
            'metacognition': '메타인지',
            'engagement': '소크라테스 참여'
        };
        return names[key] || key;
    }

    getDimensionIcon(key) {
        const icons = {
            'depth': '🌊',
            'breadth': '🌐',
            'application': '🔗',
            'metacognition': '🪞',
            'engagement': '⚡'
        };
        return icons[key] || '📊';
    }

    getProgressClass(percentage) {
        if (percentage >= 80) return 'high';
        if (percentage >= 50) return 'medium';
        return 'low';
    }
}

// Initialize dashboard when script loads
const dashboard = new TeacherDashboard();