// Session Manager Utility

class SessionManager {
    constructor(apiBaseUrl = null) {
        this.apiBaseUrl = apiBaseUrl || window.__API_BASE__ || '/api/v1';
        this.sessions = [];
        this.currentSession = null;
    }

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
            this.currentSession = result;
            return result;

        } catch (error) {
            console.error('Error creating session:', error);
            throw error;
        }
    }

    async getTeacherSessions() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/teacher/sessions`);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch sessions');
            }

            const result = await response.json();
            this.sessions = result.sessions;
            return result;

        } catch (error) {
            console.error('Error fetching sessions:', error);
            throw error;
        }
    }

    async getSessionDetails(sessionId) {
        const url = `${this.apiBaseUrl}/teacher/sessions/${sessionId}`;
        console.log('🔍 Fetching session details from:', url);

        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                mode: 'cors'
            });

            console.log('📡 Response status:', response.status);
            console.log('📡 Response headers:', [...response.headers.entries()]);

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
            console.log('✅ Session data received:', data);
            return data;

        } catch (error) {
            console.error('❌ Error fetching session details:', error);
            console.error('❌ Error type:', error.constructor.name);
            console.error('❌ Error message:', error.message);
            console.error('❌ Full error:', error);
            throw error;
        }
    }

    async endSession(sessionId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/teacher/sessions/${sessionId}/end`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to end session');
            }

            return await response.json();

        } catch (error) {
            console.error('Error ending session:', error);
            throw error;
        }
    }

    async deleteSession(sessionId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/teacher/sessions/${sessionId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete session');
            }

            return await response.json();

        } catch (error) {
            console.error('Error deleting session:', error);
            throw error;
        }
    }

    async getPublicSessionInfo(sessionId) {
        const url = `${this.apiBaseUrl}/session/${sessionId}`;
        console.log('🔍 Fetching public session info from:', url);

        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                mode: 'cors'
            });

            console.log('📡 Response status:', response.status);
            console.log('📡 Response headers:', [...response.headers.entries()]);

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
            console.log('✅ Public session data received:', data);
            return data;

        } catch (error) {
            console.error('❌ Error fetching public session info:', error);
            console.error('❌ Error type:', error.constructor.name);
            console.error('❌ Error message:', error.message);
            throw error;
        }
    }

    async joinSession(sessionId, studentInfo) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/session/${sessionId}/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(studentInfo)
            });

            const result = await response.json();

            // Check if the response indicates an error (even with 200 status)
            if (result.error) {
                const error = new Error(result.message || 'Join session failed');
                error.type = result.error;
                throw error;
            }

            if (!response.ok) {
                throw new Error(result.detail || `HTTP error! status: ${response.status}`);
            }

            return result;
        } catch (error) {
            console.error('Error joining session:', error);
            throw error;
        }
    }

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

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();

        const diffMs = now - date;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMinutes < 1) {
            return '방금 전';
        } else if (diffMinutes < 60) {
            return `${diffMinutes}분 전`;
        } else if (diffHours < 24) {
            return `${diffHours}시간 전`;
        } else if (diffDays < 7) {
            return `${diffDays}일 전`;
        } else {
            return date.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                timeZone: 'Asia/Seoul'
            });
        }
    }

    getStatusText(status) {
        return '진행 중';
    }

    getStatusColor(status) {
        return '#28a745';
    }

    getDifficultyText(difficulty) {
        const difficultyMap = {
            'easy': '쉬움',
            'normal': '보통',
            'hard': '어려움'
        };
        return difficultyMap[difficulty] || difficulty;
    }

    getDifficultyIcon(difficulty) {
        const iconMap = {
            'easy': '🌱',
            'normal': '📚',
            'hard': '🎓'
        };
        return iconMap[difficulty] || '📚';
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.SessionManager = SessionManager;
}