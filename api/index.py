"""
Vercel 서버리스 함수 진입점
"""
import os
import sys
import traceback

# Vercel 환경 플래그 설정
os.environ['VERCEL'] = '1'

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 초기화 오류 저장용
init_error = None
init_error_trace = None
app = None  # Flask app will be initialized below

# Wrap all initialization in try-except to prevent crashes
try:
    # 환경변수 체크 (초기 단계)
    if not os.environ.get('DATABASE_URL'):
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please set it in Vercel project settings: "
            "Settings → Environment Variables → Add DATABASE_URL"
        )
    
    # 앱 import 및 생성 - wrap individual imports to catch module-level errors
    try:
        from app import create_app
    except Exception as import_error:
        raise ImportError(f"Failed to import app module: {import_error}") from import_error
    
    try:
        app = create_app()
        # 초기화 성공 로그
        print("✅ Application initialized successfully")
        if app and app.config.get('SQLALCHEMY_DATABASE_URI'):
            print(f"📊 Database URI configured: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    except Exception as create_error:
        raise RuntimeError(f"Failed to create Flask app: {create_error}") from create_error
    
except ValueError as ve:
    # 환경변수 오류 등 예상 가능한 오류
    init_error = str(ve)
    init_error_trace = traceback.format_exc()
    print(f"❌ Configuration Error: {init_error}")
    print(init_error_trace)
    
    # 사용자 친화적인 오류 메시지와 함께 Flask 앱 생성
    try:
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            return jsonify({
                'error': 'Application initialization failed',
                'reason': init_error,
                'solution': {
                    'step1': 'Go to Vercel Dashboard → Your Project → Settings → Environment Variables',
                    'step2': 'Add DATABASE_URL with your PostgreSQL connection string',
                    'step3': 'Add SECRET_KEY (run: openssl rand -hex 32)',
                    'step4': 'Redeploy: vercel --prod'
                },
                'help': 'See VERCEL_ENV_SETUP.md for detailed instructions'
            }), 500
        
        @app.route('/debug')
        def debug():
            return jsonify({
                'error': init_error,
                'traceback': init_error_trace,
                'env_check': {
                    'DATABASE_URL': 'NOT SET' if not os.environ.get('DATABASE_URL') else 'SET',
                    'SECRET_KEY': 'NOT SET' if not os.environ.get('SECRET_KEY') else 'SET',
                    'VERCEL': os.environ.get('VERCEL', 'NOT SET')
                }
            }), 500
    except Exception as flask_error:
        print(f"❌ Failed to create error Flask app: {flask_error}")
        app = None
    
except Exception as e:
    # 예상치 못한 오류
    init_error = str(e)
    init_error_trace = traceback.format_exc()
    print(f"❌ Unexpected Error: {init_error}")
    print(init_error_trace)
    
    try:
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            return jsonify({
                'error': 'Application initialization failed',
                'message': init_error,
                'check': 'Please check Vercel logs for details',
                'debug_endpoint': '/debug'
            }), 500
        
        @app.route('/debug')
        def debug():
            return jsonify({
                'error': init_error,
                'traceback': init_error_trace.split('\n'),
                'env_vars': {
                    'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'NOT SET',
                    'SECRET_KEY': 'SET' if os.environ.get('SECRET_KEY') else 'NOT SET',
                    'VERCEL': os.environ.get('VERCEL')
                }
            }), 500
    except Exception as flask_error:
        print(f"❌ Failed to create error Flask app: {flask_error}")
        app = None

# Ensure app is always defined - create minimal fallback if needed
if app is None:
    try:
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        @app.route('/')
        def fallback():
            return jsonify({
                'error': 'Application initialization failed - no app instance',
                'init_error': init_error,
                'note': 'Check Vercel logs for full traceback'
            }), 500
        
        @app.route('/debug')
        def debug_fallback():
            return jsonify({
                'error': init_error,
                'traceback': init_error_trace.split('\n') if init_error_trace else None,
                'status': 'Failed to initialize application'
            }), 500
    except Exception as final_error:
        # Last resort: if we can't even import Flask, we have a serious problem
        print(f"❌ CRITICAL: Cannot import Flask: {final_error}")
        # Create a minimal WSGI-compatible handler
        def minimal_handler(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'application/json')]
            body = b'{"error":"Critical initialization failure - cannot import Flask"}'
            start_response(status, headers)
            return [body]
        handler = minimal_handler
        application = minimal_handler
    else:
        # Export Flask app for Vercel
        handler = app
        application = app
else:
    # Export Flask app for Vercel
    handler = app
    application = app

# Log handler status
print(f"✅ Handler exported: {type(handler).__name__}")
