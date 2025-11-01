#!/bin/bash

# Vercel 배포 스크립트

echo "🚀 Vercel 배포를 시작합니다..."

# Vercel CLI 설치 확인
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI가 설치되어 있지 않습니다."
    echo "설치 중: npm i -g vercel"
    npm i -g vercel
fi

# 환경 변수 확인
echo ""
echo "📋 환경 변수 확인:"
echo "DATABASE_URL: ${DATABASE_URL:+설정됨}"
echo "SECRET_KEY: ${SECRET_KEY:+설정됨}"

if [ -z "$DATABASE_URL" ] || [ -z "$SECRET_KEY" ]; then
    echo ""
    echo "⚠️  필수 환경 변수가 설정되지 않았습니다."
    echo ""
    echo "환경 변수 설정 방법:"
    echo "1. Vercel CLI로 설정:"
    echo "   vercel env add DATABASE_URL"
    echo "   vercel env add SECRET_KEY"
    echo ""
    echo "2. 또는 Vercel 대시보드에서 설정"
    echo "   프로젝트 → Settings → Environment Variables"
    echo ""
    read -p "계속하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 배포 타입 선택
echo ""
echo "배포 타입을 선택하세요:"
echo "1) 개발 환경 (preview)"
echo "2) 프로덕션 (production)"
read -p "선택 (1/2): " deploy_type

case $deploy_type in
    1)
        echo "🔨 개발 환경에 배포합니다..."
        vercel
        ;;
    2)
        echo "🚀 프로덕션에 배포합니다..."
        vercel --prod
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

echo ""
echo "✅ 배포가 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. Vercel 대시보드에서 배포 상태 확인"
echo "2. 배포된 URL로 접속하여 테스트"
echo "3. 로그 확인: vercel logs"

