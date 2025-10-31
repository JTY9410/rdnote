#!/bin/bash

# WECar 연구개발일지 Docker 시작 스크립트

echo "🐳 Starting WECar Research & Development Journal System with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Build the images
echo "Building Docker images..."
docker-compose build

# Start the containers
echo "Starting containers..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Docker containers are running successfully!"
    echo ""
    echo "📝 Application URL: http://localhost:5001"
    echo "📝 Login page: http://localhost:5001/auth/login"
    echo ""
    echo "📋 Useful commands:"
    echo "  - View logs: docker-compose logs -f"
    echo "  - Stop: docker-compose down"
    echo "  - Restart: docker-compose restart"
    echo "  - Database access: docker-compose exec db psql -U wecar_user -d wecar_db"
else
    echo "❌ Failed to start containers. Check logs: docker-compose logs"
    exit 1
fi

