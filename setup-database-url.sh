#!/bin/bash

# DATABASE_URL 설정 스크립트

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 DATABASE_URL 환경 변수 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "PostgreSQL 데이터베이스 연결 문자열을 입력하세요."
echo ""
echo "형식: postgresql://user:password@host:port/database"
echo ""
echo "예시:"
echo "  postgresql://postgres:mypassword@db.xxxxx.supabase.co:5432/postgres"
echo "  postgresql://user:pass@host.railway.app:5432/railway"
echo ""
echo "⚠️  데이터베이스가 없다면:"
echo "   1. Supabase: https://supabase.com (추천)"
echo "   2. Railway: https://railway.app"
echo "   3. Neon: https://neon.tech"
echo ""
echo "데이터베이스 URL: "

read -r DATABASE_URL

if [ -z "$DATABASE_URL" ]; then
    echo ""
    echo "❌ 입력이 없습니다. 나중에 다음 명령으로 설정할 수 있습니다:"
    echo "   vercel env add DATABASE_URL production"
    exit 1
fi

echo ""
echo "📝 DATABASE_URL 설정 중..."
echo "$DATABASE_URL" | vercel env add DATABASE_URL production --force

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ DATABASE_URL 설정 완료!"
    echo ""
    echo "다음 단계:"
    echo "1. 환경 변수 확인: vercel env ls"
    echo "2. 재배포: vercel --prod"
    echo "3. 마이그레이션 실행 (로컬에서):"
    echo "   export DATABASE_URL=\"$DATABASE_URL\""
    echo "   alembic upgrade head"
    echo "   python init_db.py"
else
    echo ""
    echo "❌ DATABASE_URL 설정 실패"
    exit 1
fi

