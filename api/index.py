"""
Vercel 서버리스 함수 진입점
"""
import os
import sys

# Vercel 환경 플래그 설정
os.environ['VERCEL'] = '1'

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import create_app
    
    # Flask 앱 생성
    app = create_app()
    
    # Vercel이 자동으로 'app'을 WSGI 앱으로 인식
    # handler = app (Vercel은 자동으로 감지)
    
except Exception as e:
    import traceback
    print(f"Error initializing app: {e}")
    print(traceback.format_exc())
    # 기본 에러 핸들러를 제공하는 간단한 앱
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.errorhandler(Exception)
    def handle_error(e):
        return jsonify({
            'error': 'Application initialization failed',
            'message': str(e)
        }), 500
    
    @app.route('/')
    def index():
        return jsonify({
            'error': 'Application failed to initialize',
            'check': 'Please check Vercel logs and environment variables'
        }), 500
