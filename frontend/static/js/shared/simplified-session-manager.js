// Simplified Session Manager for Single-Session Teacher Interface
// Based on the teacher dashboard simplification requirements

class SimplifiedSessionManager {
    constructor(apiBaseUrl = null) {
        this.apiBaseUrl = apiBaseUrl || window.__API_BASE__ || '/api/v1';
        this.qrGenerator = null; // Will be injected
        this.currentSession = null;
        this.localStorageKey = 'activeSession';
    }

    // Initialize with QR generator dependency
    setQRGenerator(qrGenerator) {
        this.qrGenerator = qrGenerator;
    }

    // LocalStorage Management
    saveSession(sessionData) {
        const sessionInfo = {
            sessionId: sessionData.session.id,
            title: sessionData.session.config.title,
            topic: sessionData.session.config.topic,
            difficulty: sessionData.session.config.difficulty,
            showScore: sessionData.session.config.show_score,
            createdAt: sessionData.session.created_at,
            lastAccessedAt: new Date().toISOString()
        };
        localStorage.setItem(this.localStorageKey, JSON.stringify(sessionInfo));
        this.currentSession = sessionData;
        return sessionInfo;
    }

    getSavedSession() {
        const saved = localStorage.getItem(this.localStorageKey);
        return saved ? JSON.parse(saved) : null;
    }

    clearSavedSession() {
        localStorage.removeItem(this.localStorageKey);
        this.currentSession = null;
    }

    // Session Validation
    async validateSession(sessionId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/teacher/sessions/${sessionId}/validate`);

            if (!response.ok) {
                console.error('Session validation failed:', response.status);
                return false;
            }

            const result = await response.json();
            return result.valid;
        } catch (error) {
            console.error('Error validating session:', error);
            return false;
        }
    }

    // Create New Session
    async createSession(sessionConfig) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/teacher/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(sessionConfig)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create session');
            }

            const result = await response.json();

            // Save to localStorage immediately
            this.saveSession(result);

            return result;

        } catch (error) {
            console.error('Error creating session:', error);
            throw error;
        }
    }

    // Archive Current Session (soft delete for new session workflow)
    async archiveCurrentSession() {
        const saved = this.getSavedSession();
        if (!saved || !saved.sessionId) {
            return true; // No session to archive
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/teacher/sessions/${saved.sessionId}/archive`, {
                method: 'POST'
            });

            if (!response.ok) {
                console.warn('Failed to archive session on server, continuing anyway');
            }

            // Clear locally regardless of server response
            this.clearSavedSession();
            return true;

        } catch (error) {
            console.warn('Error archiving session, clearing locally:', error);
            this.clearSavedSession();
            return true; // Continue with local cleanup
        }
    }

    // Get Session Details for Dashboard
    async getSessionDetails(sessionId) {
        const url = `${this.apiBaseUrl}/teacher/sessions/${sessionId}`;

        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    console.warn('Could not parse error response as JSON');
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('Error fetching session details:', error);
            throw error;
        }
    }

    // Session Initialization Logic
    async initializeSession() {
        const savedSession = this.getSavedSession();

        if (savedSession) {
            console.log('Found saved session:', savedSession);

            // Validate session is still active on server
            const isValid = await this.validateSession(savedSession.sessionId);

            if (isValid) {
                console.log('Saved session is valid, loading dashboard');
                return {
                    action: 'showDashboard',
                    sessionId: savedSession.sessionId,
                    sessionInfo: savedSession
                };
            } else {
                console.log('Saved session is invalid, clearing and showing setup');
                this.clearSavedSession();
                return { action: 'showSetup' };
            }
        } else {
            console.log('No saved session, showing setup');
            return { action: 'showSetup' };
        }
    }

    // Create Session and Show Dashboard Flow
    async createSessionAndShowDashboard(sessionConfig) {
        try {
            // Create session (this also saves to localStorage)
            const sessionData = await this.createSession(sessionConfig);

            return {
                action: 'showDashboard',
                sessionId: sessionData.session.id,
                sessionInfo: {
                    sessionId: sessionData.session.id,
                    title: sessionConfig.title,
                    topic: sessionConfig.topic,
                    difficulty: sessionConfig.difficulty,
                    showScore: sessionConfig.show_score,
                    createdAt: sessionData.session.created_at
                },
                sessionData: sessionData
            };

        } catch (error) {
            console.error('Failed to create session:', error);
            throw error;
        }
    }

    // Start New Session Flow (with confirmation)
    async startNewSession() {
        // Archive current session (if any)
        await this.archiveCurrentSession();

        return { action: 'showSetup' };
    }

    // QR Code Management
    async generateSessionQR(sessionId) {
        if (!this.qrGenerator) {
            throw new Error('QR Generator not available');
        }

        try {
            // Try to get QR from server first
            let qrImageData = null;
            try {
                const qrResponse = await fetch(`${this.apiBaseUrl}/qr/${sessionId}.png`);
                if (qrResponse.ok) {
                    const blob = await qrResponse.blob();
                    qrImageData = await new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    });
                }
            } catch (qrError) {
                console.log('Server QR not available, generating client-side');
            }

            // Generate client-side if server QR not available
            if (!qrImageData) {
                const base_url = window.location.origin;
                const session_url = `${base_url}/s/${sessionId}`;

                const qrCanvas = document.createElement('canvas');
                await this.qrGenerator.generateQRCode(qrCanvas, session_url);
                qrImageData = qrCanvas.toDataURL();
            }

            return qrImageData;

        } catch (error) {
            console.error('Failed to generate QR code:', error);
            throw error;
        }
    }

    // Utility Methods
    formatDuration(minutes) {
        if (minutes < 60) {
            return `${minutes}분`;
        } else {
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = minutes % 60;
            if (remainingMinutes === 0) {
                return `${hours}시간`;
            } else {
                return `${hours}시간 ${remainingMinutes}분`;
            }
        }
    }


    getDifficultyText(difficulty) {
        const difficultyMap = {
            'easy': '쉬움',
            'normal': '보통',
            'hard': '어려움'
        };
        return difficultyMap[difficulty] || difficulty;
    }


    calculateSessionDuration(startTime, sessionDurationMinutes = null) {
        // If server provided duration_minutes, use that
        if (sessionDurationMinutes !== null && sessionDurationMinutes !== undefined) {
            return this.formatDuration(sessionDurationMinutes);
        }

        // Fallback to client-side calculation
        const start = new Date(startTime);
        const now = new Date();
        const diffMs = now - start;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));

        return this.formatDuration(Math.max(0, diffMinutes));
    }

    formatKoreanTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('ko-KR', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.SimplifiedSessionManager = SimplifiedSessionManager;
}