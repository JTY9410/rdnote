from flask import Blueprint, render_template, send_from_directory, current_app
import os
from flask_login import login_required

help_bp = Blueprint('help', __name__)

@help_bp.route('/')
def index():
    return render_template('help/index.html')

@help_bp.route('/guno-guide')
def guno_guide():
    # Serve the integration guide HTML from project root
    project_root = os.path.abspath(os.path.join(current_app.root_path, os.pardir))
    return send_from_directory(project_root, '구노 서비스 통합 가이드.html')

