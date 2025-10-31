#!/bin/bash

# WECar 연구개발일지 애플리케이션 시작 스크립트

echo "🚀 Starting WECar Research & Development Journal System..."

# Kill any existing processes on the port
echo "Clearing port 5501..."
lsof -ti:5501 2>/dev/null | xargs kill -9 2>/dev/null

# Start the Flask application
echo "Starting Flask application on port 5501..."
nohup python3 run.py > /tmp/flask.log 2>&1 &

sleep 3

# Check if server is running
if curl -s http://localhost:5501 > /dev/null; then
    echo "✅ Server is running successfully!"
    echo ""
    echo "📝 Application URL: http://localhost:5501"
    echo "📝 Login page: http://localhost:5501/auth/login"
    echo ""
    echo "📋 To view logs: tail -f /tmp/flask.log"
    echo "📋 To stop server: killall python3"
else
    echo "❌ Server failed to start. Check logs: cat /tmp/flask.log"
fi

