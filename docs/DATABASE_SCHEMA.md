# 데이터베이스 스키마 설계

## 개요
파일 기반 저장 시스템을 PostgreSQL 데이터베이스로 마이그레이션하기 위한 스키마 설계

## 테이블 구조

### 1. teachers (교사 정보)
```sql
CREATE TABLE teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint VARCHAR(32) UNIQUE NOT NULL, -- 브라우저 핑거프린트
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2. sessions (세션 정보)
```sql
CREATE TABLE sessions (
    id VARCHAR(20) PRIMARY KEY, -- 기존 세션 ID 형식 유지
    teacher_id UUID NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    title VARCHAR(200),
    topic TEXT NOT NULL,
    description TEXT,
    difficulty VARCHAR(10) CHECK (difficulty IN ('easy', 'normal', 'hard')) DEFAULT 'normal',
    show_score BOOLEAN DEFAULT TRUE,
    time_limit INTEGER,
    max_students INTEGER,
    status VARCHAR(10) CHECK (status IN ('active', 'ended')) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE
);
```

### 3. students (학생 정보)
```sql
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(20) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    conversation_turns INTEGER DEFAULT 0,
    current_score INTEGER DEFAULT 0,
    depth_score INTEGER DEFAULT 0,
    breadth_score INTEGER DEFAULT 0,
    application_score INTEGER DEFAULT 0,
    metacognition_score INTEGER DEFAULT 0,
    engagement_score INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### 4. messages (대화 메시지)
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_id VARCHAR(20) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    message_type VARCHAR(10) CHECK (message_type IN ('user', 'assistant', 'system')) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);
```

### 5. score_records (점수 기록)
```sql
CREATE TABLE score_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    session_id VARCHAR(20) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    overall_score INTEGER NOT NULL,
    depth_score INTEGER NOT NULL,
    breadth_score INTEGER NOT NULL,
    application_score INTEGER NOT NULL,
    metacognition_score INTEGER NOT NULL,
    engagement_score INTEGER NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    evaluation_data JSONB, -- insights, growth_indicators, next_focus 등
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```


## 인덱스

```sql
-- 성능 최적화를 위한 인덱스
CREATE INDEX idx_teachers_fingerprint ON teachers(fingerprint);
CREATE INDEX idx_sessions_teacher_id ON sessions(teacher_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_students_session_id ON students(session_id);
CREATE INDEX idx_students_joined_at ON students(joined_at DESC);
CREATE INDEX idx_messages_student_id ON messages(student_id);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_score_records_student_id ON score_records(student_id);
CREATE INDEX idx_score_records_message_id ON score_records(message_id);
CREATE INDEX idx_score_records_session_id ON score_records(session_id);
CREATE INDEX idx_score_records_created_at ON score_records(created_at DESC);
```

## 데이터 관계

```
teachers (1) ──→ (N) sessions
sessions (1) ──→ (N) students
students (1) ──→ (N) messages
students (1) ──→ (N) score_records
messages (1) ──→ (N) score_records
sessions (1) ──→ (N) score_records
```

## 마이그레이션 전략

1. **기존 JSON 데이터 파싱**
   - sessions.json → sessions, teachers 테이블
   - students.json → students, messages 테이블

2. **데이터 변환 규칙**
   - teacher_fingerprint → teachers.fingerprint (신규 teacher 레코드 생성)
   - session config → sessions 컬럼들로 분할
   - student.messages → 별도 messages 테이블로 이동
   - student.progress.dimensions → 개별 점수 컬럼으로 분할

3. **실시간 통계 계산**
   - live_stats는 쿼리로 실시간 계산
   - 필요 시 캐싱 레이어 추가 고려

## 환경 변수

```env
DATABASE_URL=postgresql://username:password@host:port/database
```

## 장점

1. **데이터 정규화**: 중복 제거, 일관성 보장
2. **확장성**: 인덱스를 통한 빠른 검색
3. **관계 무결성**: 외래키 제약조건
4. **트랜잭션 지원**: 데이터 일관성 보장
5. **백업/복구**: 데이터베이스 레벨 지원
6. **동시성**: 다중 인스턴스 지원