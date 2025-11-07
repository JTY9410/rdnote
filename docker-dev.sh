#!/bin/bash

# Docker 개발 환경 자동 시작 스크립트
# 파일 변경 시 자동으로 컨테이너에 반영됩니다

echo "🚀 Starting Docker development environment..."
echo ""

# 개발 모드로 실행
export FLASK_ENV=development
export FLASK_DEBUG=1

# Docker Compose 실행 (watch 모드 활성화)
if command -v docker compose &> /dev/null; then
    # Docker Compose v2
    docker compose up --build
elif command -v docker-compose &> /dev/null; then
    # Docker Compose v1
    docker-compose up --build
else
    echo "❌ Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi



