#!/bin/bash
# Vercel 환경변수 빠른 설정 스크립트

echo "========================================="
echo "Vercel 환경변수 설정 도우미"
echo "========================================="
echo ""

# Vercel CLI 확인
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI가 설치되어 있지 않습니다."
    echo "설치: npm i -g vercel"
    exit 1
fi

echo "✅ Vercel CLI 확인 완료"
echo ""

# DATABASE_URL 입력
echo "📝 DATABASE_URL을 입력하세요:"
echo "   예시: postgresql://user:pass@host:port/db?sslmode=require"
read -p "DATABASE_URL: " DB_URL

if [ -z "$DB_URL" ]; then
    echo "❌ DATABASE_URL이 비어있습니다."
    exit 1
fi

# SECRET_KEY 생성
echo ""
echo "🔑 SECRET_KEY 생성 중..."
SECRET_KEY=$(openssl rand -hex 32)
echo "생성된 SECRET_KEY: $SECRET_KEY"
echo ""

# 환경변수 추가
echo "📤 Vercel에 환경변수 추가 중..."
echo ""

# DATABASE_URL 추가
echo "1. DATABASE_URL 추가"
vercel env add DATABASE_URL << EOF
$DB_URL
production
preview
development
EOF

# SECRET_KEY 추가
echo ""
echo "2. SECRET_KEY 추가"
vercel env add SECRET_KEY << EOF
$SECRET_KEY
production
preview
development
EOF

# FLASK_ENV 추가
echo ""
echo "3. FLASK_ENV 추가"
vercel env add FLASK_ENV << EOF
production
production
preview
development
EOF

echo ""
echo "========================================="
echo "✅ 환경변수 설정 완료!"
echo "========================================="
echo ""
echo "다음 명령으로 재배포하세요:"
echo "  vercel --prod"
echo ""
echo "또는 환경변수 목록 확인:"
echo "  vercel env ls"
echo ""

