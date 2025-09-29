/**
 * PDF 업로드 및 주제 통합 기능
 * 교사용 세션 설정 페이지에서 PDF 기반 학습 주제 생성
 */

class PDFTopicManager {
    constructor() {
        this.apiBase = window.__API_BASE__ || '/api/v1';
        this.state = {
            compressedContent: null,  // 압축된 PDF 본문
            oneSentenceTopic: null,  // 한 문장 학습 주제 (UI 노출용)
            nounTopic: null,  // 명사형 학습 주제 (QR/채팅용)
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
        this.viewCompressedContentBtn = document.getElementById('viewCompressedContentBtn');

        // 모달 요소
        this.pdfContentModal = document.getElementById('pdfContentModal');
        this.closePdfContentModal = document.getElementById('closePdfContentModal');
        this.compressedContentText = document.getElementById('compressedContentText');
        this.modalContentTitle = document.getElementById('modalContentTitle');

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

        // 압축 전문 보기 버튼 이벤트
        if (this.viewCompressedContentBtn) {
            this.viewCompressedContentBtn.addEventListener('click', this.showCompressedContentModal.bind(this));
        }

        // 모달 닫기 이벤트
        if (this.closePdfContentModal) {
            this.closePdfContentModal.addEventListener('click', this.hideCompressedContentModal.bind(this));
        }

        // 모달 배경 클릭시 닫기
        if (this.pdfContentModal) {
            this.pdfContentModal.addEventListener('click', (e) => {
                if (e.target === this.pdfContentModal) {
                    this.hideCompressedContentModal();
                }
            });
        }
    }

    // 드래그 앤 드롭 처리
    handleDragOver(e) {
        e.preventDefault();
        const target = e.currentTarget;
        target.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        const target = e.currentTarget;
        target.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        const target = e.currentTarget;
        target.classList.remove('dragover');

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

            // API 호출 (배포 환경에서 타임아웃 처리)
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30초 타임아웃

            const response = await fetch(`${this.apiBase}/teacher/analyze-pdf`, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                let errorMessage = '분석 요청 실패';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (jsonError) {
                    // JSON 파싱 실패 시 (404 HTML 페이지 등)
                    errorMessage = `서버 오류 (${response.status}): API 엔드포인트를 찾을 수 없습니다`;
                }
                throw new Error(errorMessage);
            }

            let analysisResult;
            try {
                analysisResult = await response.json();
            } catch (jsonError) {
                throw new Error('서버 응답을 처리할 수 없습니다. JSON 형식이 올바르지 않습니다.');
            }

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

            // 배포 환경에서 발생할 수 있는 오류들에 대한 구체적인 메시지
            let errorMessage = error.message;
            if (error.name === 'AbortError') {
                errorMessage = '요청 시간이 초과되었습니다. 파일 크기를 줄이거나 잠시 후 다시 시도해주세요.';
            } else if (error.message.includes('fetch')) {
                errorMessage = '네트워크 연결에 문제가 있습니다. 인터넷 연결을 확인해주세요.';
            }

            this.showError(`PDF 분석 실패: ${errorMessage}`);
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
        // PDF 분석 결과 저장 (핵심 필드만)
        this.state.compressedContent = result.compressed_content;  // 압축된 본문
        this.state.oneSentenceTopic = result.one_sentence_topic;  // 한 문장 주제
        this.state.nounTopic = result.noun_topic;  // 명사형 주제

        console.log('📄 PDF 분석 결과 저장됨:', {
            oneSentenceTopic: this.state.oneSentenceTopic,
            nounTopic: this.state.nounTopic,
            compressedContentLength: this.state.compressedContent?.length || 0
        });

        this.hideProcessingStatus();

        // 한 문장 주제를 세션 주제 필드에 설정 (UI 노출용)
        this.updateSessionTopic(result.one_sentence_topic || "학습 주제");

        // PDF 결과 제목을 명사형 주제로 변경
        const pdfResultTitle = document.getElementById('pdfResultTitle');
        if (pdfResultTitle && result.noun_topic) {
            pdfResultTitle.textContent = result.noun_topic;
        }

        // 한 문장 학습 주제 표시
        this.pdfConceptTags.innerHTML = '';
        if (result.one_sentence_topic) {
            const topicElement = document.createElement('div');
            topicElement.className = 'one-sentence-topic';
            topicElement.innerHTML = `
                <div class="topic-label">학습 주제</div>
                <div class="topic-content">${result.one_sentence_topic}</div>
            `;
            this.pdfConceptTags.appendChild(topicElement);
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
        const compressedContent = this.state.compressedContent;
        const manualContent = this.state.manualContent;

        if (!compressedContent && !manualContent) {
            // 둘 다 없으면 세션 주제 필드 비움
            this.updateSessionTopic('');
            return;
        }

        if (compressedContent && manualContent) {
            // 둘 다 있으면 통합
            await this.combineTopics(compressedContent, manualContent);
        } else if (compressedContent) {
            // PDF만 있음 - 한 문장 주제 사용
            if (this.state.oneSentenceTopic) {
                this.updateSessionTopic(this.state.oneSentenceTopic);
            }
        } else {
            // 직접 입력만 있음
            this.updateSessionTopic(manualContent);
        }
    }

    // 주제 통합
    async combineTopics(compressedContent, manualContent) {
        try {
            const response = await fetch(`${this.apiBase}/teacher/combine-topic`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    pdf_content: compressedContent,
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
            const combined = `${compressedContent}\n\n추가 관점: ${manualContent}`;
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

    // 파일 교체 처리 (오류 상태와 분석 완료 상태 공통)
    handleReplaceFile() {
        // PDF 관련 상태 초기화
        this.state.compressedContent = null;
        this.state.oneSentenceTopic = null;
        this.state.nounTopic = null;

        // 모든 UI 상태 초기화
        this.clearErrorState();
        this.hideResultCard();
        this.hideProcessingStatus();
        this.pdfUploadZone.style.display = 'flex';

        // 파일 입력 초기화
        if (this.pdfFileInput) this.pdfFileInput.value = '';

        // 태그 영역 클리어
        if (this.pdfConceptTags) this.pdfConceptTags.innerHTML = '';

        // PDF 결과 제목 초기화
        const pdfResultTitle = document.getElementById('pdfResultTitle');
        if (pdfResultTitle) {
            pdfResultTitle.textContent = 'PDF 분석 완료';
        }
    }

    // 현재 난이도 가져오기
    getDifficulty() {
        const difficultyInput = document.querySelector('input[name="difficulty"]:checked');
        return difficultyInput ? difficultyInput.value : 'normal';
    }

    // 에러 표시 (표준화된 오류 상태 사용)
    showError(message) {
        // 기존 상태 숨기기
        this.hideAllSections();
        this.pdfUploadZone.style.display = 'none';

        // 오류 상태 컨테이너 생성 또는 업데이트
        let errorContainer = document.querySelector('.pdf-error-state');
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.className = 'pdf-error-state';
            this.pdfUploadZone.parentNode.appendChild(errorContainer);
        }

        errorContainer.innerHTML = `
            <div class="error-content">
                <div class="error-icon">⚠️</div>
                <div class="error-text">
                    <h4>${message}</h4>
                    <p>여기에 PDF 파일을 다시 업로드해주세요</p>
                </div>
            </div>
        `;

        errorContainer.style.display = 'flex';
        errorContainer.style.cursor = 'pointer';

        // 업로드 전 상태와 동일한 상호작용 추가
        errorContainer.addEventListener('click', () => this.pdfFileInput.click());
        errorContainer.addEventListener('dragover', this.handleDragOver.bind(this));
        errorContainer.addEventListener('dragleave', this.handleDragLeave.bind(this));
        errorContainer.addEventListener('drop', this.handleDrop.bind(this));
    }

    // 오류 상태 숨기기
    clearErrorState() {
        const errorContainer = document.querySelector('.pdf-error-state');
        if (errorContainer) {
            errorContainer.style.display = 'none';
        }
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

    // 압축 전문 모달 표시
    showCompressedContentModal() {
        if (this.state.compressedContent && this.pdfContentModal && this.compressedContentText) {
            this.compressedContentText.textContent = this.state.compressedContent;

            // 모달 제목을 명사형 학습주제로 업데이트
            if (this.modalContentTitle && this.state.nounTopic) {
                this.modalContentTitle.textContent = this.state.nounTopic;
            }

            this.pdfContentModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }

    // 압축 전문 모달 숨기기
    hideCompressedContentModal() {
        if (this.pdfContentModal) {
            this.pdfContentModal.style.display = 'none';
            document.body.style.overflow = '';
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
            compressedContent: null,  // 압축된 PDF 본문
            oneSentenceTopic: null,  // 한 문장 학습 주제 (UI 노출용)
            nounTopic: null,  // 명사형 학습 주제 (QR/채팅용)
            manualContent: null,
            finalTopic: null,
            sourceType: 'none',
            isProcessing: false
        };

        // UI 완전 초기화 (에러 상태도 정리)
        this.clearErrorState();
        this.hideAllSections();
        this.pdfUploadZone.style.display = 'flex'; // 업로드 영역 다시 표시
        this.updateSessionTopic('');

        if (this.pdfFileInput) this.pdfFileInput.value = '';
        if (this.manualTopicInput) this.manualTopicInput.value = '';
        if (this.pdfConceptTags) this.pdfConceptTags.innerHTML = '';

        // PDF 결과 제목 초기화
        const pdfResultTitle = document.getElementById('pdfResultTitle');
        if (pdfResultTitle) {
            pdfResultTitle.textContent = 'PDF 분석 완료';
        }
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