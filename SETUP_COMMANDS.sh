#!/bin/bash
# 완전한 환경 설정 스크립트

echo "========================================="
echo "Vercel 환경변수 설정 도우미"
echo "========================================="
echo ""

# 1. PostgreSQL 연결 문자열 입력
echo "📝 PostgreSQL 연결 문자열을 입력하세요:"
echo "   (Supabase/Neon에서 복사한 것)"
echo "   형식: postgresql://user:pass@host:port/db?sslmode=require"
read -p "DATABASE_URL: " DB_URL

if [ -z "$DB_URL" ]; then
    echo "❌ DATABASE_URL이 비어있습니다."
    exit 1
fi

# 2. SECRET_KEY 사용 (이미 생성됨)
SECRET_KEY="a149467f009e36e85458a03e386803bde2becccd9a06b5dea820485324d0b850"

echo ""
echo "🔑 SECRET_KEY: $SECRET_KEY"
echo ""

# 3. 환경변수 추가 안내
echo "========================================="
echo "환경변수 추가 방법"
echo "========================================="
echo ""
echo "다음 명령을 실행하세요:"
echo ""
echo "1. DATABASE_URL 추가:"
echo "   vercel env add DATABASE_URL"
echo "   값: $DB_URL"
echo "   환경: production, preview, development 모두 선택"
echo ""
echo "2. SECRET_KEY 추가:"
echo "   vercel env add SECRET_KEY"
echo "   값: $SECRET_KEY"
echo "   환경: production, preview, development 모두 선택"
echo ""
echo "3. 확인:"
echo "   vercel env ls"
echo ""
echo "4. 재배포:"
echo "   vercel --prod"
echo ""
echo "========================================="
