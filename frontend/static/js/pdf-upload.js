/**
 * PDF 업로드 및 주제 통합 기능
 * 교사용 세션 설정 페이지에서 PDF 기반 학습 주제 생성
 */

class PDFTopicManager {
    constructor() {
        this.apiBase = window.API_BASE_URL || '/api/v1';
        this.state = {
            pdfContent: null,
            manualContent: null,
            finalTopic: null,
            sourceType: 'none', // 'pdf', 'manual', 'hybrid', 'none'
            isProcessing: false
        };

        this.lottieAnimation = null; // Lottie 애니메이션 인스턴스

        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        // PDF 업로드 관련 요소
        this.pdfUploadZone = document.getElementById('pdfUploadZone');
        this.pdfFileInput = document.getElementById('pdfFile');

        // 상태 표시 요소
        this.processingStatus = document.getElementById('pdfProcessingStatus');
        this.currentStep = document.getElementById('currentStep');
        this.lottieContainer = document.getElementById('pdfLottieContainer');

        // 결과 표시 요소
        this.resultCard = document.getElementById('pdfResultCard');
        this.pdfConceptTags = document.getElementById('pdfConceptTags');

        // 직접 입력 요소
        this.manualTopicInput = document.getElementById('manualTopicInput');

        // 버튼 요소
        this.reprocessBtn = document.getElementById('reprocessBtn');
        this.replaceFileBtn = document.getElementById('replaceFileBtn');

        // 기존 세션 주제 필드 (폴백용)
        this.sessionTopicField = document.getElementById('sessionTopic');
    }

    bindEvents() {
        // PDF 업로드 이벤트
        if (this.pdfUploadZone) {
            this.pdfUploadZone.addEventListener('click', () => this.pdfFileInput.click());
            this.pdfUploadZone.addEventListener('dragover', this.handleDragOver.bind(this));
            this.pdfUploadZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
            this.pdfUploadZone.addEventListener('drop', this.handleDrop.bind(this));
        }

        if (this.pdfFileInput) {
            this.pdfFileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }

        // 직접 입력 변경 이벤트
        if (this.manualTopicInput) {
            this.manualTopicInput.addEventListener('input', this.debounce(this.handleManualInput.bind(this), 500));
        }

        // 버튼 이벤트
        if (this.reprocessBtn) {
            this.reprocessBtn.addEventListener('click', this.handleReprocess.bind(this));
        }

        if (this.replaceFileBtn) {
            this.replaceFileBtn.addEventListener('click', this.handleReplaceFile.bind(this));
        }
    }

    // 드래그 앤 드롭 처리
    handleDragOver(e) {
        e.preventDefault();
        this.pdfUploadZone.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.pdfUploadZone.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.pdfUploadZone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFileUpload(files[0]);
        }
    }

    // 파일 선택 처리
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.handleFileUpload(file);
        }
    }

    // 파일 업로드 및 분석
    async handleFileUpload(file) {
        if (this.state.isProcessing) return;

        // 파일 유효성 검사
        if (file.type !== 'application/pdf') {
            this.showError('PDF 파일만 업로드 가능합니다.');
            return;
        }

        if (file.size > 10 * 1024 * 1024) { // 10MB
            this.showError('파일 크기가 너무 큽니다. (최대 10MB)');
            return;
        }

        this.state.isProcessing = true;
        this.showProcessingStatus();

        try {
            // FormData 생성
            const formData = new FormData();
            formData.append('pdf_file', file);
            formData.append('difficulty', this.getDifficulty());

            // 처리 단계 표시
            this.updateProcessingStep('파일 분석중...');

            // API 호출
            const response = await fetch(`${this.apiBase}/teacher/analyze-pdf`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '분석 요청 실패');
            }

            const analysisResult = await response.json();

            if (!analysisResult.success) {
                throw new Error(analysisResult.error_message || '분석 실패');
            }

            // 분석 완료
            this.updateProcessingStep('분석 완료!');

            setTimeout(() => {
                this.showAnalysisResult(analysisResult);
                this.handleTopicUpdate();
            }, 1000);

        } catch (error) {
            console.error('PDF 분석 오류:', error);
            this.showError(`PDF 분석 실패: ${error.message}`);
            this.hideProcessingStatus();
        } finally {
            this.state.isProcessing = false;
        }
    }

    // 처리 상태 표시 - 업로드 영역 숨김
    showProcessingStatus() {
        this.pdfUploadZone.style.display = 'none';
        this.hideResultCard();
        this.processingStatus.style.display = 'block';
        this.initializeLottieAnimation();
    }

    hideProcessingStatus() {
        this.processingStatus.style.display = 'none';
        this.destroyLottieAnimation();
    }

    updateProcessingStep(step) {
        this.currentStep.textContent = step;
    }

    // 분석 결과 표시
    showAnalysisResult(result) {
        this.state.pdfContent = result.summary;

        this.hideProcessingStatus();

        // PDF 분석 결과를 바로 세션 주제 필드에 설정
        this.updateSessionTopic(result.summary);

        // 주요 개념 태그 표시
        this.pdfConceptTags.innerHTML = '';
        if (result.key_concepts && result.key_concepts.length > 0) {
            result.key_concepts.forEach(concept => {
                const tag = document.createElement('span');
                tag.className = 'concept-tag';
                tag.textContent = concept;
                this.pdfConceptTags.appendChild(tag);
            });
        }

        // 분석 완료 후 결과 카드 표시 (업로드 영역은 숨김 유지)
        this.resultCard.style.display = 'block';
    }

    // 직접 입력 처리
    async handleManualInput() {
        const manualContent = this.manualTopicInput.value.trim();
        this.state.manualContent = manualContent || null;

        await this.handleTopicUpdate();
    }

    // 주제 업데이트 (통합 또는 단독 사용)
    async handleTopicUpdate() {
        const pdfContent = this.state.pdfContent;
        const manualContent = this.state.manualContent;

        if (!pdfContent && !manualContent) {
            // 둘 다 없으면 세션 주제 필드 비움
            this.updateSessionTopic('');
            return;
        }

        if (pdfContent && manualContent) {
            // 둘 다 있으면 통합
            await this.combineTopics(pdfContent, manualContent);
        } else if (pdfContent) {
            // PDF만 있음
            this.updateSessionTopic(pdfContent);
        } else {
            // 직접 입력만 있음
            this.updateSessionTopic(manualContent);
        }
    }

    // 주제 통합
    async combineTopics(pdfContent, manualContent) {
        try {
            const response = await fetch(`${this.apiBase}/teacher/combine-topic`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    pdf_content: pdfContent,
                    manual_content: manualContent,
                    difficulty: this.getDifficulty()
                })
            });

            if (!response.ok) {
                throw new Error('주제 통합 요청 실패');
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error_message || '주제 통합 실패');
            }

            this.updateSessionTopic(result.combined_topic);

        } catch (error) {
            console.error('주제 통합 오류:', error);
            // 통합 실패시 간단 결합
            const combined = `${pdfContent}\n\n추가 관점: ${manualContent}`;
            this.updateSessionTopic(combined);
        }
    }


    // 세션 주제 필드 업데이트 (기존 폼과 연동)
    updateSessionTopic(content) {
        if (this.sessionTopicField) {
            this.sessionTopicField.value = content;
        }
    }

    // 모든 섹션 숨기기
    hideAllSections() {
        this.hideProcessingStatus();
        this.hideResultCard();
    }

    // 결과 카드 숨기기
    hideResultCard() {
        if (this.resultCard) this.resultCard.style.display = 'none';
    }

    // 다시 분석 처리 (기존)
    handleReprocess() {
        this.pdfFileInput.click();
    }

    // 파일 교체 처리 (새로운 플로우)
    handleReplaceFile() {
        // 상태 초기화
        this.state.pdfContent = null;

        // UI 초기화
        this.hideResultCard();
        this.pdfUploadZone.style.display = 'block';

        // 파일 입력 초기화
        if (this.pdfFileInput) this.pdfFileInput.value = '';

        // 세션 주제 필드 초기화 (수동 입력이 없는 경우만)
        if (!this.state.manualContent) {
            this.updateSessionTopic('');
        } else {
            // 수동 입력만 남김
            this.updateSessionTopic(this.state.manualContent);
        }

        // 태그 영역 클리어
        if (this.pdfConceptTags) this.pdfConceptTags.innerHTML = '';
    }

    // 현재 난이도 가져오기
    getDifficulty() {
        const difficultyInput = document.querySelector('input[name="difficulty"]:checked');
        return difficultyInput ? difficultyInput.value : 'normal';
    }

    // 에러 표시
    showError(message) {
        // 기존 에러 메시지 제거
        const existingError = document.querySelector('.pdf-error-message');
        if (existingError) {
            existingError.remove();
        }

        // 에러 메시지 생성
        const errorDiv = document.createElement('div');
        errorDiv.className = 'pdf-error-message';
        errorDiv.style.cssText = `
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 12px;
            color: #c53030;
            font-size: 14px;
        `;
        errorDiv.textContent = message;

        // PDF 업로드 영역 다음에 추가
        this.pdfUploadZone.parentNode.insertBefore(errorDiv, this.pdfUploadZone.nextSibling);

        // 5초 후 자동 제거
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    // Lottie 애니메이션 초기화
    initializeLottieAnimation() {
        if (!this.lottieContainer || !window.lottie) {
            console.warn('Lottie not available, using fallback spinner');
            this.showFallbackSpinner();
            return;
        }

        try {
            // 기존 애니메이션 정리
            this.destroyLottieAnimation();

            // Lottie 애니메이션 로드
            this.lottieAnimation = lottie.loadAnimation({
                container: this.lottieContainer,
                renderer: 'svg',
                loop: true,
                autoplay: true,
                path: '/static/001 lottie.json'
            });

            this.lottieAnimation.addEventListener('DOMLoaded', () => {
                console.log('📄 PDF 분석 Lottie 애니메이션 로드 완료');
            });

            this.lottieAnimation.addEventListener('error', (error) => {
                console.error('Lottie 애니메이션 로드 실패:', error);
                this.showFallbackSpinner();
            });

        } catch (error) {
            console.error('Lottie 초기화 실패:', error);
            this.showFallbackSpinner();
        }
    }

    // Lottie 애니메이션 제거
    destroyLottieAnimation() {
        if (this.lottieAnimation) {
            this.lottieAnimation.destroy();
            this.lottieAnimation = null;
        }

        // 폴백 스피너 제거
        if (this.lottieContainer) {
            this.lottieContainer.innerHTML = '';
        }
    }

    // 폴백 스피너 표시
    showFallbackSpinner() {
        if (this.lottieContainer) {
            this.lottieContainer.innerHTML = '<div class="spinner"></div>';
        }
    }

    // 디바운스 유틸리티
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 상태 초기화
    reset() {
        this.state = {
            pdfContent: null,
            manualContent: null,
            finalTopic: null,
            sourceType: 'none',
            isProcessing: false
        };

        // UI 완전 초기화
        this.hideAllSections();
        this.pdfUploadZone.style.display = 'block'; // 업로드 영역 다시 표시
        this.updateSessionTopic('');

        if (this.pdfFileInput) this.pdfFileInput.value = '';
        if (this.manualTopicInput) this.manualTopicInput.value = '';
        if (this.pdfConceptTags) this.pdfConceptTags.innerHTML = '';
    }
}

// PDF 관리자 인스턴스를 전역으로 생성
let pdfTopicManager;

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    pdfTopicManager = new PDFTopicManager();
    console.log('📄 PDF 주제 관리자 초기화 완료');
});

// 전역으로 노출 (다른 스크립트에서 접근 가능)
window.PDFTopicManager = PDFTopicManager;
window.pdfTopicManager = null; // 초기화 후 할당됨

// DOM 로드 완료 시 전역 변수 할당
document.addEventListener('DOMContentLoaded', () => {
    // 약간의 지연을 두어 다른 스크립트에서 접근 가능하도록
    setTimeout(() => {
        if (pdfTopicManager) {
            window.pdfTopicManager = pdfTopicManager;
        }
    }, 100);
});