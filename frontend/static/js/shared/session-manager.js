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
        try {
            const response = await fetch(`${this.apiBaseUrl}/teacher/sessions/${sessionId}`);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch session details');
            }

            return await response.json();

        } catch (error) {
            console.error('Error fetching session details:', error);
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

    async joinSession(sessionId, studentInfo) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/session/${sessionId}/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(studentInfo)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
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
                day: 'numeric'
            });
        }
    }

    getStatusText(status) {
        const statusMap = {
            'waiting': '대기 중',
            'active': '진행 중',
            'completed': '완료됨',
            'expired': '만료됨'
        };
        return statusMap[status] || status;
    }

    getStatusColor(status) {
        const colorMap = {
            'waiting': '#ffd700',
            'active': '#28a745',
            'completed': '#6c757d',
            'expired': '#dc3545'
        };
        return colorMap[status] || '#6c757d';
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