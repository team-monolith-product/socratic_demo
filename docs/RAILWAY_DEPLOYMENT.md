# Railway 배포 가이드 - 데이터베이스 통합

## 개요
파일 기반 저장소에서 PostgreSQL 데이터베이스로 마이그레이션 후 Railway 배포 설정

## Railway 환경 변수 설정

### 필수 환경 변수

```bash
# 데이터베이스 설정
USE_DATABASE=true
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database

# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# CORS 설정
ALLOWED_ORIGINS=https://socratic-nine.vercel.app,https://yourapp.railway.app

# 포트 설정 (Railway에서 자동 설정)
PORT=$PORT
```

### Railway PostgreSQL 데이터베이스 설정

1. **Railway 프로젝트에 PostgreSQL 추가**
   ```bash
   # Railway CLI 사용
   railway add postgresql
   ```

2. **데이터베이스 URL 확인**
   - Railway 대시보드에서 PostgreSQL 서비스 선택
   - Connect 탭에서 DATABASE_URL 복사
   - 환경 변수 `DATABASE_URL`에 설정

3. **데이터베이스 URL 형식**
   ```
   postgresql+asyncpg://username:password@host:port/database
   ```

## 배포 단계

### 1. 기존 데이터 백업 (선택사항)
```bash
# 로컬에서 기존 JSON 데이터 백업
cp backend/data/sessions.json backup/
cp backend/data/students.json backup/
```

### 2. 환경 변수 설정
Railway 대시보드에서 다음 환경 변수 설정:

```
USE_DATABASE=true
DATABASE_URL=<Railway PostgreSQL URL>
OPENAI_API_KEY=<your_key>
ALLOWED_ORIGINS=https://socratic-nine.vercel.app
```

### 3. 배포
```bash
# Railway CLI로 배포
railway up

# 또는 GitHub 연동으로 자동 배포
git push origin main
```

### 4. 데이터베이스 초기화 확인
- 배포 후 로그에서 다음 메시지 확인:
  ```
  💾 Storage mode: Database
  🗄️ Initializing database...
  ✅ Database tables created/verified successfully
  ```

## 마이그레이션 (기존 데이터 이전)

### 로컬 데이터를 Railway DB로 마이그레이션

1. **로컬에서 마이그레이션 스크립트 실행**
   ```bash
   cd backend
   export DATABASE_URL="postgresql+asyncpg://..."
   export USE_DATABASE=true
   python scripts/migrate_to_database.py --migrate
   ```

2. **마이그레이션 검증**
   ```bash
   python scripts/migrate_to_database.py --test
   ```

## 모니터링

### 헬스 체크
```bash
curl https://yourapp.railway.app/health
```

### 저장소 상태 확인
```bash
curl https://yourapp.railway.app/api/v1/teacher/storage/stats
```

### 데이터베이스 연결 상태
Railway 대시보드에서 PostgreSQL 메트릭 확인

## 문제 해결

### 데이터베이스 연결 실패
1. `DATABASE_URL` 형식 확인
2. PostgreSQL 서비스 상태 확인
3. 방화벽/보안 그룹 설정 확인

### 마이그레이션 실패
1. 기존 JSON 파일 형식 확인
2. 데이터베이스 권한 확인
3. 로그에서 구체적인 오류 메시지 확인

### 성능 이슈
1. 데이터베이스 인덱스 확인
2. 쿼리 최적화 필요 시 로그 분석
3. Railway PostgreSQL 플랜 업그레이드 고려

## 백업 전략

### 자동 백업
Railway PostgreSQL은 자동 백업 제공

### 수동 백업
```bash
# PostgreSQL 덤프 생성
pg_dump $DATABASE_URL > backup.sql

# 복원
psql $DATABASE_URL < backup.sql
```

## 비용 최적화

### 개발 환경
- Railway Starter 플랜 사용
- PostgreSQL Starter (무료)

### 프로덕션 환경
- 사용량에 따른 플랜 선택
- 정기적인 데이터 정리로 스토리지 최적화

## 환경별 설정

### 개발 환경 (.env.local)
```bash
USE_DATABASE=false  # 파일 기반 개발
DATABASE_URL=sqlite+aiosqlite:///./socratic.db
```

### 프로덕션 환경 (Railway)
```bash
USE_DATABASE=true
DATABASE_URL=postgresql+asyncpg://...
```