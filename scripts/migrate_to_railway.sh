#!/bin/bash

# Railway PostgreSQL로 데이터 마이그레이션 스크립트

echo "🚄 Railway PostgreSQL 마이그레이션 시작..."

# Railway 환경 변수 가져오기
echo "📡 Railway 환경 변수 가져오는 중..."
eval "$(railway run printenv | grep DATABASE_URL)"

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL을 찾을 수 없습니다."
    echo "Railway PostgreSQL이 설정되었는지 확인하세요."
    exit 1
fi

# asyncpg 드라이버 추가
export DATABASE_URL="${DATABASE_URL/postgresql:/postgresql+asyncpg:}"
export USE_DATABASE=true

echo "🗄️ 사용할 DATABASE_URL: $DATABASE_URL"

# 백엔드 디렉토리로 이동
cd backend

# 마이그레이션 실행
echo "🔄 데이터 마이그레이션 실행 중..."
python scripts/migrate_to_database.py --migrate

echo "✅ 마이그레이션 완료!"

# 검증
echo "🔍 마이그레이션 검증 중..."
python scripts/migrate_to_database.py --test