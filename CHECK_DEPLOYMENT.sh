#!/bin/bash
# Vercel 배포 상태 확인 및 환경변수 체크 스크립트

echo "========================================="
echo "Vercel 배포 상태 확인"
echo "========================================="
echo ""

# 배포 URL
DEPLOY_URL="https://rdnote-83ozlpdrw-jeong-tai-youngs-projects.vercel.app"

echo "📊 배포된 애플리케이션:"
echo "   $DEPLOY_URL"
echo ""

echo "🔍 디버그 엔드포인트 확인 중..."
echo ""

# 디버그 엔드포인트 확인
DEBUG_RESPONSE=$(curl -s "$DEPLOY_URL/debug" 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$DEBUG_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$DEBUG_RESPONSE"
else
    echo "❌ 연결 실패"
fi

echo ""
echo "========================================="
echo "환경변수 확인"
echo "========================================="
echo ""

vercel env ls

echo ""
echo "========================================="
echo "다음 단계"
echo "========================================="
echo ""
echo "1. 환경변수가 없으면 추가:"
echo "   ./QUICK_ENV_SETUP.sh"
echo ""
echo "2. 또는 수동으로:"
echo "   vercel env add DATABASE_URL"
echo "   vercel env add SECRET_KEY"
echo ""
echo "3. 환경변수 추가 후 재배포:"
echo "   vercel --prod"
echo ""

