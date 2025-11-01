#!/bin/bash

# Vercel 환경 변수 설정 스크립트

echo "🔧 Vercel 환경 변수 설정을 시작합니다..."
echo ""

# SECRET_KEY 생성
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "✅ SECRET_KEY 생성 완료: ${SECRET_KEY:0:20}..."
echo ""

# 환경 변수 설정 안내
echo "다음 환경 변수들을 설정합니다:"
echo "1. SECRET_KEY (자동 생성됨)"
echo "2. UPLOAD_FOLDER = /tmp/uploads"
echo "3. EXPORT_FOLDER = /tmp/exports"
echo "4. DATABASE_URL (직접 입력 필요)"
echo ""

# SECRET_KEY 설정
echo "📝 SECRET_KEY 설정 중..."
echo "$SECRET_KEY" | vercel env add SECRET_KEY production --force

# UPLOAD_FOLDER 설정
echo "📝 UPLOAD_FOLDER 설정 중..."
echo "/tmp/uploads" | vercel env add UPLOAD_FOLDER production --force

# EXPORT_FOLDER 설정
echo "📝 EXPORT_FOLDER 설정 중..."
echo "/tmp/exports" | vercel env add EXPORT_FOLDER production --force

echo ""
echo "✅ 환경 변수 설정 완료!"
echo ""
echo "⚠️  DATABASE_URL은 별도로 설정해야 합니다:"
echo "   vercel env add DATABASE_URL production"
echo ""
echo "데이터베이스 URL 예시:"
echo "   postgresql://user:password@host:port/database"
echo ""
echo "무료 PostgreSQL 호스팅 옵션:"
echo "   - Supabase: https://supabase.com"
echo "   - Railway: https://railway.app"
echo "   - Neon: https://neon.tech"

