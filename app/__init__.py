from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://wecar_user:wecar_pass@localhost:5432/wecar_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    app.config['EXPORT_FOLDER'] = os.environ.get('EXPORT_FOLDER', 'exports')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
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
        from app.utils.permissions import can_access_note, can_write_note, can_delete_file, can_download
        return {
            'can_access_note': can_access_note,
            'can_write_note': can_write_note,
            'can_delete_file': can_delete_file,
            'can_download': can_download
        }
    
    # Initialize system settings on first run (after tables exist)
    # Moved to runtime to avoid startup issues
    
    return app

