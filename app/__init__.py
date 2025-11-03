from flask import Flask, redirect, url_for, render_template, jsonify
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import traceback
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
from sqlalchemy import text

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Vercel/serverless 환경에서는 DATABASE_URL 필수
        if os.environ.get('VERCEL'):
            logger.error("DATABASE_URL environment variable is required in Vercel/serverless environment")
            raise ValueError("DATABASE_URL must be set for serverless deployment")
        else:
            # 로컬 개발 환경에서만 SQLite 사용
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'wecar_db.sqlite')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            logger.info(f"Using SQLite database at: {db_path}")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        logger.info("Using PostgreSQL database from DATABASE_URL")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Ensure error handlers work even in debug mode
    # Flask's debug error handler will be overridden by our handlers
    app.config['PROPAGATE_EXCEPTIONS'] = False
    
    # Session configuration for better compatibility
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Vercel serverless compatibility: use /tmp for ephemeral storage
    # Note: Files in /tmp are deleted after function execution
    # For production, use external storage (S3, Cloudflare R2, etc.)
    if os.environ.get('VERCEL'):
        app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
        app.config['EXPORT_FOLDER'] = os.environ.get('EXPORT_FOLDER', '/tmp/exports')
    else:
        app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
        app.config['EXPORT_FOLDER'] = os.environ.get('EXPORT_FOLDER', 'exports')
    
    # SQLAlchemy connection pool settings
    # pool_pre_ping: 연결 전 상태 확인하여 끊어진 연결 자동 재연결
    # pool_recycle: 연결을 주기적으로 재사용하여 타임아웃 방지
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    
    if os.environ.get('VERCEL'):
        # Vercel/serverless 환경: 연결 풀 최소화 (서버리스는 함수당 1 연결)
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,  # 연결 전 ping으로 상태 확인
            'pool_recycle': 300,   # 5분마다 연결 재사용
            'pool_size': 1,
            'max_overflow': 0,
            'poolclass': None,  # 기본 연결 풀 사용
            'connect_args': {
                'connect_timeout': 10,  # 연결 타임아웃 10초
                'sslmode': 'require' if 'sslmode' not in db_uri else None,  # PostgreSQL SSL
            }
        }
    elif db_uri.startswith('sqlite'):
        # SQLite 로컬 개발 환경
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {
                'check_same_thread': False,  # Allow multi-threaded access
                'timeout': 20,  # SQLite timeout
            },
            'pool_pre_ping': False,  # Not needed for SQLite
        }
    else:
        # PostgreSQL 로컬 환경 설정
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 5,
            'max_overflow': 10,
            'connect_args': {
                'connect_timeout': 10,
            }
        }
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    # Use 'basic' protection to avoid issues with serverless environments
    login_manager.session_protection = 'basic'  # Changed from 'strong' for better compatibility
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID, with error handling"""
        try:
            if not user_id:
                logger.debug("load_user called with None user_id")
                return None
            from app.models.user import User
            user_id_int = int(user_id)
            user = User.query.get(user_id_int)
            if user:
                logger.debug(f"Loaded user: {user.email} (ID: {user_id_int})")
            else:
                logger.warning(f"User not found with ID: {user_id_int}")
            return user
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user_id in load_user: {user_id}, error: {e}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error in load_user: {e}")
            logger.error(traceback.format_exc())
            try:
                db.session.rollback()
            except Exception:
                pass
            return None
        except Exception as e:
            logger.error(f"Unexpected error in load_user: {e}")
            logger.error(traceback.format_exc())
            return None
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized access"""
        logger.warning("Unauthorized access attempt")
        from flask import redirect, url_for, flash
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('auth.login'))
    
    # Register blueprints with error handling
    try:
        from app.blueprints.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except Exception as e:
        logger.error(f"Failed to register auth blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    except Exception as e:
        logger.error(f"Failed to register dashboard blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.profile import profile_bp
        app.register_blueprint(profile_bp, url_prefix='/profile')
    except Exception as e:
        logger.error(f"Failed to register profile blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.workspaces import workspaces_bp
        app.register_blueprint(workspaces_bp, url_prefix='/workspaces')
    except Exception as e:
        logger.error(f"Failed to register workspaces blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.notes import notes_bp
        app.register_blueprint(notes_bp, url_prefix='/notes')
    except Exception as e:
        logger.error(f"Failed to register notes blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.folders import folders_bp
        app.register_blueprint(folders_bp, url_prefix='')
    except Exception as e:
        logger.error(f"Failed to register folders blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.files import files_bp
        app.register_blueprint(files_bp, url_prefix='')
    except Exception as e:
        logger.error(f"Failed to register files blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.export import export_bp
        app.register_blueprint(export_bp, url_prefix='')
    except Exception as e:
        logger.error(f"Failed to register export blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except Exception as e:
        logger.error(f"Failed to register admin blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.help import help_bp
        app.register_blueprint(help_bp, url_prefix='/help')
    except Exception as e:
        logger.error(f"Failed to register help blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.comments import comments_bp
        app.register_blueprint(comments_bp, url_prefix='')
    except Exception as e:
        logger.error(f"Failed to register comments blueprint: {e}")
        logger.error(traceback.format_exc())
    
    try:
        from app.blueprints.webhooks import webhooks_bp
        app.register_blueprint(webhooks_bp, url_prefix='')
    except Exception as e:
        logger.error(f"Failed to register webhooks blueprint: {e}")
        logger.error(traceback.format_exc())
    
    # Request error handlers - catch errors during request processing
    @app.before_request
    def before_request():
        """각 요청 전 데이터베이스 연결 확인 및 복구"""
        try:
            # 데이터베이스 연결 상태 확인 및 자동 복구
            try:
                # 간단한 쿼리로 연결 상태 확인
                db.session.execute(text('SELECT 1'))
            except (OperationalError, DisconnectionError) as db_error:
                logger.warning(f"Database connection lost, attempting to reconnect: {db_error}")
                try:
                    # 세션 롤백
                    db.session.rollback()
                    # 연결 풀 재사용 시도 (pool_pre_ping이 자동으로 처리)
                    db.session.close()
                    # 새 세션으로 다시 연결 시도
                    db.session.execute(text('SELECT 1'))
                    logger.info("Database connection recovered")
                except Exception as reconnect_error:
                    logger.error(f"Failed to reconnect to database: {reconnect_error}")
                    # 연결 실패해도 요청은 계속 진행 (나중에 더 구체적인 오류 처리)
        except Exception as e:
            # 다른 오류는 로그만 기록하고 계속 진행
            logger.debug(f"Error in before_request (non-critical): {e}")
    
    @app.teardown_request
    def teardown_request(exception):
        """Handle cleanup after each request"""
        if exception:
            logger.error(f"Exception in request: {exception}")
            logger.error(traceback.format_exc())
            try:
                db.session.rollback()
            except Exception:
                pass
        # Don't auto-commit here - let views handle their own commits
        # Flask-SQLAlchemy handles session management
    
    # Test route for debugging (can be removed in production)
    @app.route('/health')
    def health_check():
        """Health check endpoint with database status"""
        
        health_status = {
            'status': 'ok',
            'application': 'running',
            'database': 'unknown'
        }
        
        try:
            # 데이터베이스 연결 테스트
            db.session.execute(text('SELECT 1'))
            health_status['database'] = 'connected'
            status_code = 200
        except (OperationalError, DisconnectionError) as db_error:
            health_status['status'] = 'degraded'
            health_status['database'] = 'disconnected'
            health_status['database_error'] = str(db_error)[:200]
            logger.warning(f"Health check: Database connection failed - {db_error}")
            status_code = 503  # Service Unavailable
        except Exception as e:
            health_status['status'] = 'error'
            health_status['database'] = 'error'
            health_status['error'] = str(e)[:200]
            logger.error(f"Error in health check: {e}")
            status_code = 500
        
        return jsonify(health_status), status_code
    
    # Root route
    @app.route('/')
    def index():
        try:
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.error(f"Error in root route: {e}")
            logger.error(traceback.format_exc())
            return '<h1>Application Error</h1><p>Please contact administrator.</p>', 500
    
    # Make utility functions available to templates
    @app.context_processor
    def inject_permissions():
        try:
            from app.utils.permissions import can_access_note, can_write_note, can_delete_file, can_download
            return {
                'can_access_note': can_access_note,
                'can_write_note': can_write_note,
                'can_delete_file': can_delete_file,
                'can_download': can_download
            }
        except Exception as e:
            logger.error(f"Error in inject_permissions: {e}")
            return {}
    
    # Global error handlers - register these AFTER everything else to catch all errors
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import request
        # Ignore common 404 requests that don't need logging
        ignored_paths = ['/favicon.ico', '/robots.txt', '/apple-touch-icon.png', 
                        '/apple-touch-icon-precomposed.png', '/favicon.png']
        
        if request.path in ignored_paths:
            # These are common browser/SEO requests, just return 404 without logging
            return '', 404
        
        # Only log non-ignored 404 errors as debug level (reduces noise)
        logger.debug(f"404 error for path: {request.path} - {error}")
        
        try:
            return render_template('errors/404.html'), 404
        except Exception:
            return '<h1>404 - Page Not Found</h1><p>The page you are looking for does not exist.</p>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Internal Server Error: {error}")
        logger.error(traceback.format_exc())
        try:
            db.session.rollback()
        except Exception:
            pass
        try:
            return render_template('errors/500.html'), 500
        except Exception:
            return '<h1>500 - Internal Server Error</h1><p>An internal error occurred. Please try again later.</p>', 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all unhandled exceptions - This must be last"""
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        
        # Rollback any database session
        try:
            db.session.rollback()
        except Exception:
            pass
        
        # Return appropriate response based on request type
        from flask import request
        try:
            # Check if this is a 404 or other HTTPException
            from werkzeug.exceptions import HTTPException
            if isinstance(e, HTTPException):
                return e
            
            if hasattr(request, 'is_json') and request.is_json:
                return jsonify({'error': 'An internal error occurred', 'message': str(e)}), 500
            else:
                return render_template('errors/500.html'), 500
        except Exception as render_error:
            # Fallback if template rendering fails
            logger.error(f"Error rendering error template: {render_error}")
            return '<h1>500 - Internal Server Error</h1><p>An internal error occurred. Please try again later.</p>', 500
    
    # Initialize system settings on first run (after tables exist)
    # Moved to runtime to avoid startup issues
    
    return app

