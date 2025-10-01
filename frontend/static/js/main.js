class TopicInputHandler {
    constructor() {
        // 동적으로 API 베이스 URL 설정
        this.apiBase = this.getApiBase();
        this.init();
        this.initAnimations();
    }

    getApiBase() {
        if (typeof window !== 'undefined' && window.__API_BASE__) {
            console.log('Using API_BASE from config:', window.__API_BASE__);
            return window.__API_BASE__;
        }
        console.warn('No API_BASE found in config, using relative path');
        return '/api/v1';
    }

    init() {
        const form = document.getElementById('topicForm');
        const loading = document.getElementById('loading');

        if (form) {
            form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Add input validation and animations
        this.initInputInteractions();
        this.initCardAnimations();
    }

    initAnimations() {
        // Fade in animations on page load
        this.animatePageLoad();

        // Add scroll-based animations
        this.initScrollAnimations();
    }

    animatePageLoad() {
        // Animate hero section
        const heroTitle = document.querySelector('.hero-title');
        const heroSubtitle = document.querySelector('.hero-subtitle');
        const mainContent = document.querySelector('.main-content');
        const features = document.querySelector('.features-section');

        if (heroTitle) {
            heroTitle.style.opacity = '0';
            heroTitle.style.transform = 'translateY(30px)';
            setTimeout(() => {
                heroTitle.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                heroTitle.style.opacity = '1';
                heroTitle.style.transform = 'translateY(0)';
            }, 200);
        }

        if (heroSubtitle) {
            heroSubtitle.style.opacity = '0';
            heroSubtitle.style.transform = 'translateY(30px)';
            setTimeout(() => {
                heroSubtitle.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                heroSubtitle.style.opacity = '1';
                heroSubtitle.style.transform = 'translateY(0)';
            }, 400);
        }

        if (mainContent) {
            mainContent.style.opacity = '0';
            mainContent.style.transform = 'translateY(40px)';
            setTimeout(() => {
                mainContent.style.transition = 'all 1s cubic-bezier(0.4, 0, 0.2, 1)';
                mainContent.style.opacity = '1';
                mainContent.style.transform = 'translateY(0)';
            }, 600);
        }
    }

    initScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observe feature cards
        document.querySelectorAll('.feature-card').forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(40px)';
            card.style.transition = `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${index * 0.1}s`;
            observer.observe(card);
        });
    }

    initInputInteractions() {
        const topicInput = document.getElementById('topicInput');

        if (topicInput) {
            // Add character counter
            this.addCharacterCounter(topicInput);

            // Add dynamic placeholder
            this.initDynamicPlaceholder(topicInput);

            // Auto-resize functionality
            this.initAutoResize(topicInput);
        }
    }

    addCharacterCounter(input) {
        const wrapper = input.closest('.input-wrapper');
        if (!wrapper) return;

        const counter = document.createElement('div');
        counter.className = 'character-counter';
        counter.style.cssText = `
            position: absolute;
            bottom: 12px;
            right: 16px;
            font-size: 12px;
            color: var(--color-text-secondary);
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        wrapper.appendChild(counter);

        const updateCounter = () => {
            const length = input.value.length;
            const maxLength = 1000;
            counter.textContent = `${length}/${maxLength}`;

            if (length > maxLength * 0.8) {
                counter.style.color = 'var(--color-primary)';
            } else {
                counter.style.color = 'var(--color-text-secondary)';
            }
        };

        input.addEventListener('input', updateCounter);
        input.addEventListener('focus', () => {
            counter.style.opacity = '1';
            updateCounter();
        });
        input.addEventListener('blur', () => {
            if (input.value.length === 0) {
                counter.style.opacity = '0';
            }
        });
    }

    initDynamicPlaceholder(input) {
        const placeholders = [
            '예: 기후변화의 원인과 해결방안',
            '예: 인공지능의 윤리적 문제',
            '예: 우주 탐사의 의미와 가치',
            '예: 미래 에너지원의 종류와 특징',
            '예: 생명공학의 발전과 사회적 영향'
        ];

        let currentIndex = 0;
        const cyclePlaceholder = () => {
            if (input.value.length === 0) {
                input.style.opacity = '0.7';
                setTimeout(() => {
                    input.placeholder = placeholders[currentIndex];
                    input.style.opacity = '1';
                    currentIndex = (currentIndex + 1) % placeholders.length;
                }, 200);
            }
        };

        input.addEventListener('focus', () => {
            clearInterval(input.placeholderInterval);
        });

        input.addEventListener('blur', () => {
            if (input.value.length === 0) {
                input.placeholderInterval = setInterval(cyclePlaceholder, 3000);
            }
        });

        // Start placeholder cycling
        if (input.value.length === 0) {
            input.placeholderInterval = setInterval(cyclePlaceholder, 3000);
        }
    }

    initAutoResize(textarea) {
        const resize = () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
        };

        textarea.addEventListener('input', resize);
        window.addEventListener('resize', resize);
    }

    initCardAnimations() {
        // Add hover animations to option buttons
        document.querySelectorAll('.option-button').forEach(button => {
            button.addEventListener('mouseenter', (e) => {
                if (!button.classList.contains('disabled')) {
                    button.style.transform = 'translateY(-2px) scale(1.02)';
                }
            });

            button.addEventListener('mouseleave', (e) => {
                const input = button.previousElementSibling;
                if (!input.checked) {
                    button.style.transform = 'translateY(0) scale(1)';
                }
            });
        });

        // Add ripple effect to primary button
        const primaryButton = document.querySelector('.primary-button');
        if (primaryButton) {
            primaryButton.addEventListener('click', this.createRippleEffect);
        }
    }

    createRippleEffect(e) {
        const button = e.currentTarget;
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            width: 100px;
            height: 100px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: translate(-50%, -50%) scale(0);
            animation: ripple 0.6s ease-out;
            left: ${x}px;
            top: ${y}px;
            pointer-events: none;
        `;

        button.appendChild(ripple);

        // Create keyframes if not exists
        if (!document.querySelector('#ripple-keyframes')) {
            const style = document.createElement('style');
            style.id = 'ripple-keyframes';
            style.textContent = `
                @keyframes ripple {
                    to {
                        transform: translate(-50%, -50%) scale(4);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const topic = formData.get('topic').trim();
        const contentType = formData.get('contentType');
        const difficulty = formData.get('difficulty');
        const scoreDisplay = formData.get('scoreDisplay');
        
        if (!topic) {
            alert('학습 주제를 입력해주세요.');
            return;
        }
        
        this.showLoading();
        
        try {
            // 1. 주제 검증
            await this.validateTopic(topic, contentType);
            
            // 2. 채팅 페이지로 이동
            this.navigateToChat(topic, difficulty, scoreDisplay);
            
        } catch (error) {
            this.hideLoading();
            console.error('Error:', error);
            alert(error.message || '오류가 발생했습니다. 다시 시도해주세요.');
        }
    }
    
    async validateTopic(topic, contentType) {
        const response = await fetch(`${this.apiBase}/topic/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic_content: topic,
                content_type: contentType
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '주제 검증에 실패했습니다.');
        }
        
        return await response.json();
    }
    
    navigateToChat(topic, difficulty, scoreDisplay) {
        // URL 파라미터로 주제, 난이도, 점수 표시 옵션 전달
        const params = new URLSearchParams({
            topic: topic,
            difficulty: difficulty,
            showScore: scoreDisplay === 'show'
        });
        window.location.href = `/pages/socratic-chat.html?${params.toString()}`;
    }
    
    showLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'flex';
        }
    }
    
    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    new TopicInputHandler();
});

// 유용한 유틸리티 함수들
const utils = {
    // 텍스트 길이 제한 확인
    validateTextLength(text, maxLength = 1000) {
        return text.length <= maxLength;
    },

    // 안전한 HTML 인코딩
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
