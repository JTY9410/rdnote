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
    
    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.profile import profile_bp
    from app.blueprints.workspaces import workspaces_bp
    from app.blueprints.notes import notes_bp
    from app.blueprints.folders import folders_bp
    from app.blueprints.files import files_bp
    from app.blueprints.export import export_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.help import help_bp
    from app.blueprints.comments import comments_bp
    from app.blueprints.webhooks import webhooks_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(workspaces_bp, url_prefix='/workspaces')
    app.register_blueprint(notes_bp, url_prefix='/notes')
    app.register_blueprint(folders_bp, url_prefix='')
    app.register_blueprint(files_bp, url_prefix='')
    app.register_blueprint(export_bp, url_prefix='')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(help_bp, url_prefix='/help')
    app.register_blueprint(comments_bp, url_prefix='')
    app.register_blueprint(webhooks_bp, url_prefix='')
    
    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
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
    
    # Global error handlers
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
        """Handle all unhandled exceptions"""
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
            if request.is_json:
                return jsonify({'error': 'An internal error occurred', 'message': str(e)}), 500
            else:
                return render_template('errors/500.html'), 500
        except Exception:
            # Fallback if template rendering fails
            return '<h1>500 - Internal Server Error</h1><p>An internal error occurred. Please try again later.</p>', 500
    
    # Initialize system settings on first run (after tables exist)
    # Moved to runtime to avoid startup issues
    
    return app

