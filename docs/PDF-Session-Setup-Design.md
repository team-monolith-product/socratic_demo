# PDF 기반 세션 설정 기능 설계

## 개요
교사용 setup 페이지의 학습 주제 설정을 PDF 업로드 중심으로 개편하여, PDF 분석으로 생성된 3문단 요약을 메인으로 하고 추가적인 직접 입력도 병행할 수 있는 유연한 시스템을 설계한다. 두 입력 모두 활용하여 더 풍부한 소크라테스 대화를 지원한다.

## 1. 시스템 아키텍처

### 1.1 전체 워크플로우
```
[세션 제목 입력]
+
[PDF 업로드(메인)] + [직접 입력(보조, 선택)]
→
[텍스트 추출] → [내용 분석] → [3문단 요약]
→
[통합 학습 주제 생성] → [세션 시작]
```

### 1.2 학습 주제 통합 전략
- **PDF만 있는 경우**: PDF 분석 결과만 사용
- **직접 입력만 있는 경우**: 사용자 입력만 사용
- **둘 다 있는 경우**: PDF 분석을 메인으로 하고 직접 입력을 보조 맥락으로 활용

### 1.3 구성 요소
- **Frontend**: PDF 업로드 UI 컴포넌트
- **Backend API**: PDF 처리 및 분석 엔드포인트
- **PDF Processing Service**: 텍스트 추출 및 요약 서비스
- **AI Service**: 내용 분석 및 요약 생성
- **Session Service**: 기존 세션 생성 로직과 통합

## 2. 데이터 모델 설계

### 2.1 새로운 모델 추가

#### PdfAnalysisRequest
```python
class PdfAnalysisRequest(BaseModel):
    pdf_file: UploadFile
    difficulty: str = "normal"  # 요약 난이도 조절용
```

#### PdfAnalysisResult
```python
class PdfAnalysisResult(BaseModel):
    original_text: str
    summary: str  # 3문단 요약 (학습 주제로 사용됨)
    key_concepts: List[str]
    learning_objectives: List[str]
    estimated_duration: int  # 분 단위
    success: bool
    error_message: Optional[str] = None
```

#### SessionConfig 확장
```python
class SessionConfig(BaseModel):
    title: str
    topic: str
    description: Optional[str] = None
    difficulty: str = "normal"
    show_score: bool = True
    # 통합 학습 주제를 위한 새로운 필드
    source_type: str = "manual"  # "manual", "pdf", "hybrid"
    pdf_content: Optional[str] = None  # PDF 분석 3문단 요약
    manual_content: Optional[str] = None  # 사용자 직접 입력
    combined_topic: Optional[str] = None  # 최종 통합된 학습 주제
    key_concepts: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
```

## 3. API 설계

### 3.1 PDF 분석 엔드포인트
```python
@router.post("/teacher/analyze-pdf")
async def analyze_pdf(
    pdf_file: UploadFile = File(...),
    difficulty: str = Form("normal")
) -> PdfAnalysisResult
```

### 3.2 학습 주제 통합 엔드포인트
```python
@router.post("/teacher/combine-topic")
async def combine_topic_content(
    pdf_content: Optional[str] = None,
    manual_content: Optional[str] = None,
    difficulty: str = "normal"
) -> Dict[str, str]
```

### 3.3 세션 생성은 기존 엔드포인트 확장
기존 `POST /teacher/sessions` 엔드포인트를 사용하되, SessionConfig에 통합된 학습 주제 정보를 전달

## 4. PDF 처리 서비스 설계

### 4.1 PDFProcessingService
```python
class PDFProcessingService:
    async def extract_text_from_pdf(self, pdf_file: UploadFile) -> str:
        """PDF에서 텍스트 추출"""
        pass

    async def validate_pdf_content(self, text: str) -> bool:
        """교육 콘텐츠로서의 적합성 검증"""
        pass

    async def analyze_and_summarize(self, text: str, difficulty: str) -> PdfAnalysisResult:
        """AI를 사용한 내용 분석 및 3문단 요약 생성"""
        pass

    async def combine_topic_sources(
        self,
        pdf_content: Optional[str],
        manual_content: Optional[str],
        difficulty: str
    ) -> str:
        """PDF 분석 결과와 직접 입력을 통합한 최종 학습 주제 생성"""
        pass
```

### 4.2 텍스트 추출 로직
- **라이브러리**: PyPDF2 또는 pdfplumber 사용
- **파일 크기 제한**: 최대 10MB
- **페이지 제한**: 최대 50페이지
- **텍스트 길이 제한**: 최대 50,000자

### 4.3 AI 분석 및 요약 로직

#### PDF 분석 프롬프트
```python
async def generate_summary_and_analysis(self, content: str, difficulty: str) -> Dict:
    system_prompt = """
    당신은 교육 콘텐츠 분석 전문가입니다.
    주어진 PDF 내용을 분석하여 소크라테스식 대화를 위한 학습 주제를 생성하세요:

    1. 핵심 내용을 3문단으로 요약 (각 문단 3-4문장)
       - 학생들이 탐구하고 토론할 수 있는 주제 형태로 구성
       - 소크라테스식 질문을 유도할 수 있는 내용으로 작성
    2. 주요 학습 개념 5개 추출
    3. 학습 목표 3개 제시 (토론 및 탐구 중심)
    4. 예상 학습 시간 추정

    난이도: {difficulty}
    """
```

#### 통합 주제 생성 프롬프트
```python
async def combine_topic_sources(self, pdf_content: str, manual_content: str, difficulty: str) -> str:
    system_prompt = """
    당신은 교육 과정 설계 전문가입니다.
    PDF 분석 결과와 교사의 직접 입력을 통합하여 완전한 소크라테스 학습 주제를 생성하세요:

    전략:
    1. PDF 내용을 메인 주제로 사용
    2. 직접 입력을 보조 맥락이나 추가 관점으로 활용
    3. 두 내용을 자연스럽게 연결하여 통합된 학습 주제 생성
    4. 소크라테스식 질문과 탐구를 위한 구조로 작성

    PDF 내용: {pdf_content}
    교사 추가 입력: {manual_content}
    난이도: {difficulty}
    """
```

## 5. 프론트엔드 UI 설계

### 5.1 UI 구성 요소

#### 새로운 학습 주제 설정 UI
```html
<div class="session-info-section">
    <h2 class="section-title">세션 정보</h2>

    <!-- 세션 제목 (기존 유지) -->
    <div class="apple-form-group">
        <label for="sessionTitle" class="apple-label">세션 제목</label>
        <input id="sessionTitle" name="title" class="apple-input"
               placeholder="코들중학교 1학년 3반" maxlength="50" required />
    </div>

    <!-- 학습 주제 설정 (PDF 메인) -->
    <div class="apple-form-group">
        <label class="apple-label">학습 주제 설정</label>

        <!-- PDF 업로드 영역 (메인) -->
        <div class="pdf-upload-main">
            <div class="pdf-upload-zone" id="pdfUploadZone">
                <div class="upload-content">
                    <div class="upload-icon">📄</div>
                    <div class="upload-text">
                        <h4>PDF 파일을 업로드하여 자동으로 학습 주제 생성</h4>
                        <p>최대 10MB, 50페이지까지 지원 • AI가 내용을 분석하여 3문단 요약</p>
                    </div>
                </div>
                <input type="file" id="pdfFile" accept=".pdf" hidden>
            </div>

            <!-- PDF 분석 진행 상태 -->
            <div class="pdf-processing-status" id="pdfProcessingStatus" style="display: none;">
                <div class="processing-indicator">
                    <div class="spinner"></div>
                    <div class="processing-text">
                        <div class="current-step" id="currentStep">PDF 분석 중...</div>
                        <div class="step-detail" id="stepDetail">텍스트를 추출하고 있습니다</div>
                    </div>
                </div>
            </div>

            <!-- PDF 분석 결과 미리보기 -->
            <div class="pdf-result-card" id="pdfResultCard" style="display: none;">
                <div class="result-header">
                    <h4>📄 PDF 분석 완료</h4>
                    <button type="button" class="btn btn-ghost btn-sm" id="reprocessBtn">다시 분석</button>
                </div>

                <div class="pdf-generated-content">
                    <textarea id="pdfGeneratedTopic" class="apple-textarea pdf-content"
                             rows="5" placeholder="PDF 분석 결과가 여기에 표시됩니다"></textarea>
                </div>

                <div class="content-metadata">
                    <div class="metadata-item">
                        <strong>주요 개념:</strong>
                        <div class="concept-tags" id="pdfConceptTags"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 구분선과 추가 입력 옵션 -->
        <div class="topic-divider">
            <div class="divider-line"></div>
            <div class="divider-text">또는</div>
            <div class="divider-line"></div>
        </div>

        <!-- 직접 입력 영역 (보조) -->
        <div class="manual-input-auxiliary">
            <div class="manual-input-header">
                <label for="manualTopicInput" class="auxiliary-label">
                    추가 학습 내용이나 관점 입력 (선택)
                </label>
                <div class="input-hint">PDF와 함께 활용하거나 단독으로 사용 가능</div>
            </div>

            <textarea id="manualTopicInput" name="manual_topic" class="apple-textarea manual-content"
                     placeholder="추가하고 싶은 학습 내용, 특별한 관점, 또는 강조하고 싶은 부분을 입력하세요"
                     rows="3"></textarea>
        </div>

        <!-- 최종 통합 주제 미리보기 -->
        <div class="final-topic-preview" id="finalTopicPreview" style="display: none;">
            <div class="preview-header">
                <h4>🎯 최종 학습 주제</h4>
                <div class="topic-source" id="topicSource">PDF 내용 + 추가 입력 통합</div>
            </div>

            <div class="final-topic-content">
                <textarea id="finalTopic" name="topic" class="apple-textarea final-content"
                         rows="5" readonly></textarea>
            </div>

            <div class="preview-actions">
                <button type="button" class="btn btn-secondary btn-sm" id="editFinalTopicBtn">수정</button>
                <button type="button" class="btn btn-primary btn-sm" id="regenerateTopicBtn">다시 생성</button>
            </div>
        </div>
    </div>
</div>
```

### 5.2 인터랙션 플로우

#### 기본 플로우
1. **세션 제목 입력**: 사용자가 직접 세션 제목 입력 (기존 동일)
2. **PDF 업로드**: 드래그 앤 드롭 또는 클릭으로 파일 선택 (메인 방식)
3. **자동 분석**: PDF 텍스트 추출 → AI 분석 → 3문단 요약 생성
4. **PDF 결과 확인**: 생성된 학습 주제와 주요 개념 미리보기
5. **추가 입력 (선택)**: 직접 입력란에 보조 내용 또는 관점 추가
6. **통합 주제 생성**: PDF + 직접 입력 내용을 AI가 통합
7. **최종 확인**: 통합된 학습 주제 미리보기 및 수정
8. **세션 시작**: 기존 플로우로 세션 생성

#### 상황별 플로우
**PDF만 사용하는 경우:**
- PDF 업로드 → 분석 완료 → 바로 세션 시작

**직접 입력만 사용하는 경우:**
- PDF 업로드 건너뛰고 직접 입력만 작성 → 세션 시작

**PDF + 직접 입력 병행:**
- PDF 분석 → 추가 입력 → 통합 주제 생성 → 세션 시작

## 6. 백엔드 구현 상세

### 6.1 새로운 서비스 파일
```
backend/app/services/pdf_processing_service.py
backend/app/services/topic_integration_service.py
```

### 6.2 의존성 추가
```python
# requirements.txt에 추가
PyPDF2==3.0.1
pdfplumber==0.9.0
python-multipart==0.0.6  # 파일 업로드용
```

### 6.3 설정 파일 업데이트
```python
# config.py
class Settings(BaseSettings):
    # 기존 설정...

    # PDF 처리 설정
    MAX_PDF_SIZE_MB: int = 10
    MAX_PDF_PAGES: int = 50
    MAX_TEXT_LENGTH: int = 50000
    ALLOWED_PDF_TYPES: List[str] = [".pdf"]

    # AI 분석 설정
    SUMMARY_TARGET_PARAGRAPHS: int = 3
    SUMMARY_SENTENCES_PER_PARAGRAPH: int = 4
    MAX_KEY_CONCEPTS: int = 5
```

### 6.4 에러 처리
```python
class PDFProcessingError(Exception):
    """PDF 처리 관련 오류"""
    pass

class PDFTooLargeError(PDFProcessingError):
    """PDF 파일 크기 초과"""
    pass

class PDFTextExtractionError(PDFProcessingError):
    """텍스트 추출 실패"""
    pass

class InvalidPDFContentError(PDFProcessingError):
    """부적절한 PDF 내용"""
    pass
```

## 7. 보안 및 검증

### 7.1 파일 검증
- **MIME 타입 검증**: application/pdf만 허용
- **파일 크기 제한**: 10MB 이하
- **악성 파일 스캔**: PDF 구조 검증
- **내용 필터링**: 부적절한 콘텐츠 감지

### 7.2 텍스트 검증
- **언어 감지**: 한국어/영어 콘텐츠 확인
- **교육 적합성**: 교육 콘텐츠로서의 적합성 검증
- **길이 제한**: 너무 짧거나 긴 텍스트 필터링

## 8. 성능 고려사항

### 8.1 비동기 처리
- PDF 텍스트 추출: 별도 스레드에서 처리
- AI 분석: OpenAI API 호출 최적화
- 진행 상태: WebSocket 또는 Server-Sent Events로 실시간 업데이트

### 8.2 캐싱 전략
- PDF 텍스트 추출 결과 임시 캐싱
- AI 분석 결과 캐싱 (동일 내용 재분석 방지)
- 세션별 PDF 데이터 관리

### 8.3 리소스 관리
- 업로드된 PDF 파일 임시 저장 및 자동 삭제
- 메모리 사용량 모니터링
- 동시 처리 요청 수 제한

## 9. 테스트 전략

### 9.1 단위 테스트
- PDF 텍스트 추출 정확성
- AI 요약 품질 검증
- 세션 생성 로직 테스트

### 9.2 통합 테스트
- 전체 워크플로우 테스트
- 다양한 PDF 유형 테스트
- 오류 상황 처리 테스트

### 9.3 성능 테스트
- 대용량 PDF 처리 시간
- 동시 업로드 처리 성능
- 메모리 사용량 측정

## 10. 배포 및 모니터링

### 10.1 배포 고려사항
- PDF 처리 라이브러리 서버 환경 설치
- OpenAI API 키 환경 변수 설정
- 파일 업로드 임시 디렉토리 권한 설정

### 10.2 모니터링 메트릭
- PDF 업로드 성공/실패율
- 텍스트 추출 성공률
- AI 분석 응답 시간
- 생성된 세션 품질 피드백

## 11. JavaScript 인터랙션 로직

### 11.1 핵심 이벤트 핸들러
```javascript
// PDF 파일 업로드 처리
async function handlePdfUpload(file) {
    showProcessingStatus();

    try {
        const pdfAnalysis = await analyzePdf(file);
        showPdfResult(pdfAnalysis);

        // 직접 입력이 있으면 통합 주제 생성
        const manualContent = getManualInput();
        if (manualContent) {
            const combinedTopic = await combineTopicSources(pdfAnalysis.summary, manualContent);
            showFinalTopic(combinedTopic);
        } else {
            // PDF만 있는 경우 PDF 결과를 최종 주제로 사용
            showFinalTopic(pdfAnalysis.summary, 'pdf');
        }
    } catch (error) {
        showError(error.message);
    }
}

// 직접 입력 변경 처리
async function handleManualInput() {
    const manualContent = getManualInput();
    const pdfContent = getPdfContent();

    if (pdfContent && manualContent) {
        // PDF + 직접 입력 통합
        const combinedTopic = await combineTopicSources(pdfContent, manualContent);
        showFinalTopic(combinedTopic, 'hybrid');
    } else if (manualContent) {
        // 직접 입력만
        showFinalTopic(manualContent, 'manual');
    }
}
```

### 11.2 상태 관리
```javascript
const topicState = {
    pdfContent: null,
    manualContent: null,
    finalTopic: null,
    sourceType: 'none' // 'pdf', 'manual', 'hybrid'
};
```

## 12. 향후 확장 가능성

### 12.1 추가 파일 형식 지원
- Word 문서 (.docx)
- PowerPoint (.pptx)
- 이미지 OCR (jpg, png)

### 12.2 고급 통합 기능
- 다중 PDF 업로드 및 통합 분석
- 주제별 자동 세션 분할 제안
- 교사 스타일 학습 및 개인화

### 12.3 피드백 시스템
- PDF 분석 품질에 대한 교사 평가
- 통합 주제 생성 만족도 수집
- AI 프롬프트 개선을 위한 데이터 수집

이 설계를 통해 PDF 업로드를 메인으로 하고 직접 입력을 보조 수단으로 활용하는 유연하고 실용적인 학습 주제 설정 시스템을 구현할 수 있습니다.