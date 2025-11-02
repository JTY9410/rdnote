from flask import Flask, redirect, url_for, render_template, jsonify
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import traceback
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://wecar_user:wecar_pass@localhost:5432/wecar_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Ensure error handlers work even in debug mode
    # Flask's debug error handler will be overridden by our handlers
    app.config['PROPAGATE_EXCEPTIONS'] = False
    
    # Vercel serverless compatibility: use /tmp for ephemeral storage
    # Note: Files in /tmp are deleted after function execution
    # For production, use external storage (S3, Cloudflare R2, etc.)
    if os.environ.get('VERCEL'):
        app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
        app.config['EXPORT_FOLDER'] = os.environ.get('EXPORT_FOLDER', '/tmp/exports')
    else:
        app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
        app.config['EXPORT_FOLDER'] = os.environ.get('EXPORT_FOLDER', 'exports')
    
    # SQLAlchemy connection pool settings for serverless
    if os.environ.get('VERCEL'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 1,
            'max_overflow': 0
        }
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID, with error handling"""
        try:
            if not user_id:
                return None
            from app.models.user import User
            user_id_int = int(user_id)
            return User.query.get(user_id_int)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user_id in load_user: {user_id}, error: {e}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error in load_user: {e}")
            db.session.rollback()
            return None
        except Exception as e:
            logger.error(f"Unexpected error in load_user: {e}")
            logger.error(traceback.format_exc())
            return None
    
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
        try:
            # Ensure database session is available
            pass
        except Exception as e:
            logger.error(f"Error in before_request: {e}")
            logger.error(traceback.format_exc())
    
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
        """Simple health check endpoint"""
        try:
            return jsonify({'status': 'ok', 'message': 'Application is running'}), 200
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
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
        logger.warning(f"404 error: {error}")
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

